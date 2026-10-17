"""Convert the repository's CnOcr 1.2 DenseNet/GRU weights without importing MXNet.

Only the dense float32 NDArray v2 format and this model architecture are supported.
Training losses are deliberately excluded. No model downloads or retraining occur.
"""
import ast
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


def read_params(path):
    data = Path(path).read_bytes()
    offset = 0

    def read(fmt):
        nonlocal offset
        parser = struct.Struct('<' + fmt)
        value = parser.unpack_from(data, offset)
        offset += parser.size
        return value

    magic, reserved, count = read('QQQ')
    if (magic, reserved) != (0x112, 0):
        raise ValueError('Unsupported MXNet parameter file')
    arrays = []
    for _ in range(count):
        magic, storage, ndim = read('IIi')
        if magic != 0xF993FAC9 or storage != 0 or not 0 < ndim <= 4:
            raise ValueError('Expected dense NDArray v2')
        shape = read('q' * ndim)
        device, device_id, dtype = read('iii')
        if dtype != 0 or any(dim <= 0 for dim in shape):
            raise ValueError('Expected float32 weights')
        size = int(np.prod(shape))
        arrays.append(np.frombuffer(data, dtype='<f4', count=size, offset=offset).reshape(shape).copy())
        offset += size * 4
    name_count, = read('Q')
    if name_count != count:
        raise ValueError('Parameter name count mismatch')
    names = []
    for _ in range(count):
        size, = read('Q')
        names.append(data[offset:offset + size].decode().split(':', 1)[1])
        offset += size
    if offset != len(data) or len(set(names)) != count:
        raise ValueError('Unexpected parameter payload')
    return dict(zip(names, arrays))


def fingerprint(root, epoch):
    prefix = root / 'cnocr-v1.2.0-densenet-lite-gru'
    paths = [Path(f'{prefix}-symbol.json'), Path(f'{prefix}-{epoch:04d}.params'), root / 'label_cn.txt']
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.read_bytes())
    return digest.hexdigest()


def convert(root, epoch, destination):
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    root, destination = Path(root), Path(destination)
    prefix = root / 'cnocr-v1.2.0-densenet-lite-gru'
    source = json.loads(Path(f'{prefix}-symbol.json').read_text())['nodes']
    params = read_params(f'{prefix}-{epoch:04d}.params')
    nodes, tensors = [], {}

    def constant(name, value):
        tensors[name] = numpy_helper.from_array(np.asarray(value), name)
        return name

    def op(kind, inputs, output, **attrs):
        nodes.append(helper.make_node(kind, inputs, [output], name=output, **attrs))
        return output

    # DenseNet feature extractor; stop before the MXNet-specific reshape/RNN packing.
    last = next(i for i, node in enumerate(source) if node['op'] == 'expand_dims') - 1
    if source[last]['op'] != 'Reshape':
        raise ValueError('Unsupported feature extractor')
    for node in source[:last]:
        kind, name, attrs = node['op'], node['name'], node.get('attrs', {})
        inputs = [source[i]['name'] for i, port, version in node['inputs']]
        if kind == 'null':
            if name != 'data':
                constant(name, params[name])
        elif kind == 'Convolution':
            pad = list(ast.literal_eval(attrs['pad']))
            op('Conv', inputs, name, kernel_shape=list(ast.literal_eval(attrs['kernel'])),
               strides=list(ast.literal_eval(attrs['stride'])), pads=pad + pad,
               dilations=list(ast.literal_eval(attrs['dilate'])), group=int(attrs['num_group']))
        elif kind == 'BatchNorm':
            if attrs['fix_gamma'] != 'False' or attrs['axis'] != '1':
                raise ValueError('Unsupported BatchNorm')
            op('BatchNormalization', inputs, name, epsilon=float(attrs['eps']))
        elif kind == 'Activation' and attrs['act_type'] == 'relu':
            op('Relu', inputs, name)
        elif kind == 'Concat':
            op('Concat', inputs, name, axis=int(attrs['dim']))
        elif kind == 'Pooling' and attrs['pool_type'] == 'max' and attrs['pooling_convention'] == 'valid':
            pad = list(ast.literal_eval(attrs['pad']))
            op('MaxPool', inputs, name, kernel_shape=list(ast.literal_eval(attrs['kernel'])),
               strides=list(ast.literal_eval(attrs['stride'])), pads=pad + pad)
        else:
            raise ValueError(f'Unsupported operator: {node}')

    feature = source[last - 1]['name']
    rnn = next(node for node in source if node['op'] == 'RNN')
    if (rnn['attrs']['mode'], rnn['attrs']['num_layers'], rnn['attrs']['bidirectional']) != ('gru', '1', 'True'):
        raise ValueError('Expected one bidirectional GRU layer')
    packed = source[rnn['inputs'][1][0]]
    weights = [params[source[source[i]['inputs'][0][0]]['name']] for i, _, _ in packed['inputs']]
    hidden = int(rnn['attrs']['state_size'])
    channels = weights[0].shape[1]
    op('Reshape', [feature, constant('feature_shape', np.array([0, channels, -1], dtype=np.int64))], 'feature')
    op('Transpose', ['feature'], 'sequence', perm=[2, 0, 1])

    # MXNet/cuDNN gates are reset/update/new; ONNX uses update/reset/new.
    def reorder(value):
        reset, update, new = np.split(value, 3)
        return np.concatenate([update, reset, new], axis=0)

    constant('gru_W', np.stack([reorder(weights[0]), reorder(weights[2])]))
    constant('gru_R', np.stack([reorder(weights[1]), reorder(weights[3])]))
    constant('gru_B', np.stack([np.concatenate([reorder(weights[4]), reorder(weights[5])]),
                                np.concatenate([reorder(weights[6]), reorder(weights[7])])]))
    op('GRU', ['sequence', 'gru_W', 'gru_R', 'gru_B'], 'gru', hidden_size=hidden,
       direction='bidirectional', linear_before_reset=1)
    op('Transpose', ['gru'], 'gru_ordered', perm=[0, 2, 1, 3])
    op('Reshape', ['gru_ordered', constant('gru_shape', np.array([0, 0, -1], dtype=np.int64))], 'encoded')
    constant('fc_W', params['pred_fc_weight'].T.copy())
    constant('fc_B', params['pred_fc_bias'])
    op('MatMul', ['encoded', 'fc_W'], 'logits0')
    op('Add', ['logits0', 'fc_B'], 'logits')
    op('Softmax', ['logits'], 'probabilities', axis=2)
    graph = helper.make_graph(nodes, root.name,
        [helper.make_tensor_value_info('data', TensorProto.FLOAT, ['batch', 1, 32, 'width'])],
        [helper.make_tensor_value_info('probabilities', TensorProto.FLOAT, ['time', 'batch', len(params['pred_fc_bias'])])],
        list(tensors.values()))
    model = helper.make_model(graph, producer_name='alas-macos', opset_imports=[helper.make_opsetid('', 13)])
    model.ir_version = 8
    helper.set_model_props(model, {'source_sha256': fingerprint(root, epoch)})
    onnx.checker.check_model(model, full_check=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.onnx.tmp')
    onnx.save(model, temporary)
    temporary.replace(destination)
    return destination


if __name__ == '__main__':
    repo = Path(__file__).resolve().parents[2]
    for name, epoch in [('azur_lane', 15), ('azur_lane_jp', 20), ('cnocr', 39), ('jp', 125), ('tw', 63)]:
        print(convert(repo / 'bin/cnocr_models' / name, epoch,
                      Path(__file__).parent / 'models' / f'{name}.onnx'))
