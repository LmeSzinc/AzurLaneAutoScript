"""
Convert MXNet cnocr checkpoints to ONNX format.

Builds equivalent ONNX graphs directly from the MXNet symbol JSON and
parameter files.  MXNet's built-in ONNX exporter cannot handle the
hybridized bidirectional GRU (internal ops _rnn_param_concat + RNN),
so the graph is reconstructed node-by-node.

Output is written alongside the source checkpoint as model.onnx.

The MODELS list at the bottom of this file defines which models to
convert.  Each entry specifies the model name, directory, checkpoint
prefix, and epoch.  Edit this list to add or remove models.

Notes:
- MXNet GRU gate order is [r, z, h]; ONNX expects [z, r, h].
- MXNet Reshape shape values -2, -3 (relative dimensions) are rewritten 
  because ONNX only supports -1.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import onnx
from onnx import helper, TensorProto, numpy_helper

import mxnet as mx

OPSET = 13
FLOAT = TensorProto.FLOAT
INT64 = TensorProto.INT64


def parse_tuple(s):
    """Parse '(1, 2)' or '()' string into tuple of ints."""
    s = s.strip().strip('()')
    if not s:
        return ()
    return tuple(int(x.strip()) for x in s.split(','))


def ndarr(arr):
    """numpy array -> ONNX initializer."""
    return numpy_helper.from_array(arr.astype(np.float32))


def shape_init(name, vals):
    """Create an INT64 initializer for shape/axes."""
    tensor = numpy_helper.from_array(np.array(vals, dtype=np.int64), name=name)
    return tensor


class ONNXBuilder:
    def __init__(self, model_name):
        self.model_name = model_name
        self.nodes = []
        self.initializers = []
        self.name_counter = [0]
        # Maps MXNet node name -> ONNX tensor name
        self.name_map = {}
        self.eps = 1e-5

    def new_name(self, base):
        self.name_counter[0] += 1
        return f'{base}_{self.name_counter[0]}'

    def resolve(self, mxnet_ref):
        """
        Args:
            mxnet_ref is either a node index (int) or a node name (str).

        Return ONNX tensor name for an MXNet output, or None.
        """
        if isinstance(mxnet_ref, int):
            # Look up node name by index
            if 0 <= mxnet_ref < len(self.nodes_json):
                mxnet_ref = self.nodes_json[mxnet_ref]['name']
            else:
                return None
        return self.name_map.get(mxnet_ref)

    def make_conv(self, node, arg_params):
        attrs = node['attrs']
        name = node['name']
        mx_in = self.resolve(node['inputs'][0][0])
        if mx_in is None:
            return False
        # Weight is always input[1] (a param node)
        w_node_idx = node['inputs'][1][0]
        w_name = self.nodes_json[w_node_idx]['name']
        weight = arg_params[w_name]
        w_tensor = self.new_name(w_name)
        self.initializers.append(ndarr(weight.asnumpy()))
        # Note: ndarr above loses name; rebuild with name
        self.initializers[-1] = numpy_helper.from_array(weight.asnumpy(), name=w_tensor)

        kernel = parse_tuple(attrs['kernel'])
        stride = parse_tuple(attrs['stride'])
        pad = parse_tuple(attrs['pad'])
        dilate = parse_tuple(attrs['dilate'])
        groups = int(attrs['num_group'])

        out = self.new_name(name)
        # ONNX pads: [top, left, bottom, right] = [ph, pw, ph, pw]
        pads = [pad[0], pad[1], pad[0], pad[1]] if len(pad) == 2 else list(pad) * 2
        conv = helper.make_node(
            'Conv', [mx_in, w_tensor], [out],
            name=name,
            kernel_shape=list(kernel),
            strides=list(stride),
            pads=pads,
            dilations=list(dilate),
            group=groups,
        )
        self.nodes.append(conv)
        self.name_map[name] = out
        return True

    def make_batchnorm(self, node, arg_params, aux_params):
        attrs = node['attrs']
        name = node['name']
        mx_in = self.resolve(node['inputs'][0][0])
        if mx_in is None:
            return False
        eps = float(attrs['eps'])

        gamma_name = self.nodes_json[node['inputs'][1][0]]['name']
        beta_name = self.nodes_json[node['inputs'][2][0]]['name']
        mean_name = self.nodes_json[node['inputs'][3][0]]['name']
        var_name = self.nodes_json[node['inputs'][4][0]]['name']

        gamma_t = self.new_name(gamma_name)
        beta_t = self.new_name(beta_name)
        mean_t = self.new_name(mean_name)
        var_t = self.new_name(var_name)
        for t, key in [(gamma_t, gamma_name), (beta_t, beta_name),
                       (mean_t, mean_name), (var_t, var_name)]:
            src = arg_params.get(key)
            if src is None:
                src = aux_params.get(key)
            self.initializers.append(numpy_helper.from_array(src.asnumpy().astype(np.float32), name=t))

        out = self.new_name(name)
        bn = helper.make_node(
            'BatchNormalization',
            [mx_in, gamma_t, beta_t, mean_t, var_t], [out],
            name=name, epsilon=eps,
        )
        self.nodes.append(bn)
        self.name_map[name] = out
        return True

    def make_relu(self, node):
        name = node['name']
        mx_in = self.resolve(node['inputs'][0][0])
        if mx_in is None:
            return False
        out = self.new_name(name)
        relu = helper.make_node('Relu', [mx_in], [out], name=name)
        self.nodes.append(relu)
        self.name_map[name] = out
        return True

    def make_concat(self, node):
        name = node['name']
        axis = int(node['attrs']['dim'])
        mx_inputs = [self.resolve(i[0]) for i in node['inputs']]
        if any(x is None for x in mx_inputs):
            return False
        out = self.new_name(name)
        concat = helper.make_node('Concat', mx_inputs, [out], name=name, axis=axis)
        self.nodes.append(concat)
        self.name_map[name] = out
        return True

    def make_pooling(self, node):
        attrs = node['attrs']
        name = node['name']
        mx_in = self.resolve(node['inputs'][0][0])
        if mx_in is None:
            return False
        pool_type = attrs['pool_type']
        kernel = parse_tuple(attrs['kernel'])
        stride = parse_tuple(attrs['stride'])
        pad = parse_tuple(attrs['pad'])

        out = self.new_name(name)
        pads = [pad[0], pad[1], pad[0], pad[1]] if len(pad) == 2 else list(pad) * 2
        if pool_type == 'max':
            pool = helper.make_node(
                'MaxPool', [mx_in], [out], name=name,
                kernel_shape=list(kernel), strides=list(stride), pads=pads,
            )
        elif pool_type == 'avg':
            pool = helper.make_node(
                'AveragePool', [mx_in], [out], name=name,
                kernel_shape=list(kernel), strides=list(stride), pads=pads,
            )
        else:
            raise ValueError(f'Unknown pool_type: {pool_type}')
        self.nodes.append(pool)
        self.name_map[name] = out
        return True

    def make_reshape(self, node):
        name = node['name']
        shape_str = node['attrs']['shape']
        shape = parse_tuple(shape_str)
        mx_in = self.resolve(node['inputs'][0][0])
        if mx_in is None:
            return False

        # Convert MXNet shape notation to ONNX-compatible
        # -2, -3, -4 (relative dims) are not supported by ONNX; handled by caller
        onnx_shape = []
        for s in shape:
            if s >= 0 or s == -1:
                onnx_shape.append(s)
            else:
                # Unsupported relative dim — caller should have rewritten these
                raise ValueError(f'Unsupported shape value {s} in {name}')

        out = self.new_name(name)
        shape_t = self.new_name(f'{name}_shape')
        self.initializers.append(shape_init(shape_t, onnx_shape))
        reshape = helper.make_node('Reshape', [mx_in, shape_t], [out], name=name)
        self.nodes.append(reshape)
        self.name_map[name] = out
        return True

    def make_unsqueeze(self, node):
        name = node['name']
        axis = int(node['attrs']['axis'])
        mx_in = self.resolve(node['inputs'][0][0])
        if mx_in is None:
            return False
        out = self.new_name(name)
        axes_t = self.new_name(f'{name}_axes')
        self.initializers.append(shape_init(axes_t, [axis]))
        unsq = helper.make_node('Unsqueeze', [mx_in, axes_t], [out], name=name)
        self.nodes.append(unsq)
        self.name_map[name] = out
        return True

    def make_squeeze(self, node):
        name = node['name']
        axis = int(node['attrs']['axis'])
        mx_in = self.resolve(node['inputs'][0][0])
        if mx_in is None:
            return False
        out = self.new_name(name)
        axes_t = self.new_name(f'{name}_axes')
        self.initializers.append(shape_init(axes_t, [axis]))
        sq = helper.make_node('Squeeze', [mx_in, axes_t], [out], name=name)
        self.nodes.append(sq)
        self.name_map[name] = out
        return True

    def make_transpose(self, node):
        name = node['name']
        perm = parse_tuple(node['attrs']['axes'])
        mx_in = self.resolve(node['inputs'][0][0])
        if mx_in is None:
            return False
        out = self.new_name(name)
        tr = helper.make_node('Transpose', [mx_in], [out], name=name, perm=list(perm))
        self.nodes.append(tr)
        self.name_map[name] = out
        return True

    def make_dropout(self, node):
        # Inference: identity
        name = node['name']
        mx_in = self.resolve(node['inputs'][0][0])
        if mx_in is None:
            return False
        self.name_map[name] = mx_in
        return True

    def make_gemm(self, node, arg_params):
        name = node['name']
        mx_in = self.resolve(node['inputs'][0][0])
        if mx_in is None:
            return False
        w_node_idx = node['inputs'][1][0]
        w_name = self.nodes_json[w_node_idx]['name']
        b_node_idx = node['inputs'][2][0]
        b_name = self.nodes_json[b_node_idx]['name']

        w_t = self.new_name(w_name)
        b_t = self.new_name(b_name)
        self.initializers.append(numpy_helper.from_array(arg_params[w_name].asnumpy().astype(np.float32), name=w_t))
        self.initializers.append(numpy_helper.from_array(arg_params[b_name].asnumpy().astype(np.float32), name=b_t))

        out = self.new_name(name)
        # Y = X @ W^T + b  (transB=1)
        gemm = helper.make_node('Gemm', [mx_in, w_t, b_t], [out], name=name, transB=1, alpha=1.0, beta=1.0)
        self.nodes.append(gemm)
        self.name_map[name] = out
        return True

    def build(self, sym_dict, arg_params, aux_params, seq_len, hidden_dim, img_width):
        self.nodes_json = sym_dict['nodes']
        node_map = {node['name']: node for node in self.nodes_json}

        # Find input node (data)
        data_node = self.nodes_json[0]
        # Dynamic width: batch and width are free dimensions
        graph_input = helper.make_tensor_value_info('data', FLOAT, [None, 1, 32, None])
        self.name_map['data'] = 'data'

        # Walk nodes in order, handling each op
        for idx, node in enumerate(self.nodes_json):
            op = node.get('op', 'null')
            name = node.get('name', '')

            if op == 'null':
                # Parameter node (weight/data) — no-op
                continue
            if op == '_zeros':
                # Initial hidden state for RNN — handled in GRU section
                continue
            # Skip MXNet nodes that we replace with a dynamic-width-friendly
            # equivalent. The MXNet reshape(0,-3,0) + expand_dims + squeeze +
            # transpose chain has different 0-index semantics than ONNX and
            # doesn't support dynamic width.
            if name in ('densenet0_reshape0', 'densenet0_expand_dims0',
                        'dropout0_fwd', 'crnn0_squeeze0', 'crnn0_transpose0'):
                if name == 'densenet0_reshape0':
                    self.make_post_densenet(node)
                continue
            if op == 'Reshape':
                # For GRU param reshapes (gru0_reshape*), skip — they're for
                # MXNet's internal RNN param packing which we bypass.
                if name.startswith('gru0_reshape'):
                    continue
                # For reshape0 (the final reshape before FC): (-3, -2) -> (-1, hidden_dim)
                if name == 'reshape0':
                    mx_in = self.resolve(node['inputs'][0][0])
                    out = self.new_name(name)
                    shape_t = self.new_name(f'{name}_shape')
                    self.initializers.append(shape_init(shape_t, [-1, hidden_dim]))
                    self.nodes.append(helper.make_node('Reshape', [mx_in, shape_t], [out], name=name))
                    self.name_map[name] = out
                    continue
                self.make_reshape(node)
            elif op == 'Convolution':
                self.make_conv(node, arg_params)
            elif op == 'BatchNorm':
                self.make_batchnorm(node, arg_params, aux_params)
            elif op == 'Activation':
                self.make_relu(node)
            elif op == 'Concat':
                self.make_concat(node)
            elif op == 'Pooling':
                self.make_pooling(node)
            elif op == 'expand_dims':
                self.make_unsqueeze(node)
            elif op == 'squeeze':
                self.make_squeeze(node)
            elif op == 'transpose':
                self.make_transpose(node)
            elif op == 'Dropout':
                self.make_dropout(node)
            elif op == 'FullyConnected':
                self.make_gemm(node, arg_params)
            elif op == '_rnn_param_concat':
                # Bypassed — GRU built from raw params in make_gru()
                continue
            elif op == 'RNN':
                self.make_gru(node, arg_params)
            else:
                print(f'  WARNING: unhandled op {op} ({name})')

        # Find the pred_fc output tensor name
        pred_fc_node = node_map['pred_fc']
        pred_fc_out = self.name_map.get('pred_fc')

        # Add softmax
        softmax_out = 'softmax_output'
        sm = helper.make_node('Softmax', [pred_fc_out], [softmax_out], name='softmax', axis=-1)
        self.nodes.append(sm)

        graph_output = helper.make_tensor_value_info(softmax_out, FLOAT, [None, None])

        graph = helper.make_graph(
            self.nodes,
            f'{self.model_name}_graph',
            [graph_input],
            [graph_output],
            initializer=self.initializers,
        )
        model = helper.make_model(graph, opset_imports=[helper.make_opsetid('', OPSET)])
        model.ir_version = 7
        return model

    def make_post_densenet(self, node):
        """
        Replace MXNet's reshape+expand_dims+dropout+squeeze+transpose chain
        with a dynamic-width-friendly equivalent.

        MXNet DenseNet output: (batch, 256, 2, seq)  where seq = W/4
        Target GRU input:      (seq, batch, 512)

        Sequence:
          1. transpose (0, 3, 1, 2): (batch, seq, 256, 2)
          2. reshape   (0, 0, -1):   (batch, seq, 512)   [flatten 256*2]
          3. transpose (1, 0, 2):    (seq, batch, 512)
        """
        name = node['name']
        mx_in = self.resolve(node['inputs'][0][0])  # DenseNet pool output
        if mx_in is None:
            return False

        # 1. transpose (batch, 256, 2, seq) -> (batch, seq, 256, 2)
        t1 = self.new_name(f'{name}_t1')
        self.nodes.append(helper.make_node('Transpose', [mx_in], [t1],
                                           name=f'{name}_t1', perm=[0, 3, 1, 2]))

        # 2. reshape (batch, seq, 256*2=512)
        t2 = self.new_name(f'{name}_t2')
        shape_t = self.new_name(f'{name}_shape')
        self.initializers.append(shape_init(shape_t, [0, 0, -1]))
        self.nodes.append(helper.make_node('Reshape', [t1, shape_t], [t2],
                                           name=f'{name}_t2'))

        # 3. transpose (seq, batch, 512) — the GRU input layout
        t3 = self.new_name(f'{name}_t3')
        self.nodes.append(helper.make_node('Transpose', [t2], [t3],
                                           name=f'{name}_t3', perm=[1, 0, 2]))

        # Store as crnn0_transpose0 output so the RNN node can consume it
        self.name_map['crnn0_transpose0'] = t3
        return True

    def make_gru(self, node, arg_params):
        """
        Build ONNX bidirectional GRU from raw forward/backward params.

        MXNet RNN op consumes (data, params_concat, initial_h).
        Bypass the internal param packing and build ONNX GRU directly:
          X: (seq_len, batch, 512)
          W: (2, 384, 512)  [fwd_i2h, bwd_i2h]
          R: (2, 384, 128)  [fwd_h2h, bwd_h2h]
          B: (2, 768)       [fwd[i2h_bias,h2h_bias], bwd[...]]
          direction=bidirectional, linear_before_reset=0
        """
        name = node['name']
        mx_in = self.resolve(node['inputs'][0][0])  # transposed DenseNet output
        if mx_in is None:
            return False

        # Derive GRU dims from actual params (architecture is densenet-lite-gru)
        i2h0 = arg_params['gru0_l0_i2h_weight'].asnumpy()
        hidden = i2h0.shape[0] // 3  # 3*hidden, hidden = 128
        input_size = i2h0.shape[1]
        # MXNet GRU gate order is [r, z, h]; ONNX GRU expects [z, r, h].
        # Empirical finding: reorder (0<->1) + linear_before_reset=1 matches MXNet.
        idx = np.array([1, 0, 2])

        def reorder_gates(mat):
            # mat shape (3*hidden, ...) or (3*hidden,)
            if mat.ndim == 1:
                return mat.reshape(3, hidden)[idx].reshape(-1)
            else:
                return mat.reshape(3, hidden, -1)[idx].reshape(-1, mat.shape[-1])

        # Collect forward/backward GRU params
        fwd_i2h = reorder_gates(arg_params['gru0_l0_i2h_weight'].asnumpy())  # (384, 512)
        fwd_h2h = reorder_gates(arg_params['gru0_l0_h2h_weight'].asnumpy())  # (384, 128)
        fwd_i2h_b = reorder_gates(arg_params['gru0_l0_i2h_bias'].asnumpy())  # (384,)
        fwd_h2h_b = reorder_gates(arg_params['gru0_l0_h2h_bias'].asnumpy())  # (384,)
        bwd_i2h = reorder_gates(arg_params['gru0_r0_i2h_weight'].asnumpy())
        bwd_h2h = reorder_gates(arg_params['gru0_r0_h2h_weight'].asnumpy())
        bwd_i2h_b = reorder_gates(arg_params['gru0_r0_i2h_bias'].asnumpy())
        bwd_h2h_b = reorder_gates(arg_params['gru0_r0_h2h_bias'].asnumpy())

        # ONNX GRU weights: W (2, 3h, input), R (2, 3h, h), B (2, 6h)
        W = np.stack([fwd_i2h, bwd_i2h]).astype(np.float32)  # (2, 384, 512)
        R = np.stack([fwd_h2h, bwd_h2h]).astype(np.float32)  # (2, 384, 128)
        B = np.stack([np.concatenate([fwd_i2h_b, fwd_h2h_b]),
                      np.concatenate([bwd_i2h_b, bwd_h2h_b])]).astype(np.float32)  # (2, 768)

        w_t = self.new_name('gru_W')
        r_t = self.new_name('gru_R')
        b_t = self.new_name('gru_B')
        self.initializers.append(numpy_helper.from_array(W, name=w_t))
        self.initializers.append(numpy_helper.from_array(R, name=r_t))
        self.initializers.append(numpy_helper.from_array(B, name=b_t))

        # GRU output Y: (seq_len, num_directions, batch, hidden)
        y_t = self.new_name('gru_Y')
        gru = helper.make_node(
            'GRU', [mx_in, w_t, r_t, b_t], [y_t],
            name=name,
            hidden_size=hidden,
            direction='bidirectional',
            linear_before_reset=1,
        )
        self.nodes.append(gru)

        # Transform Y (seq_len, 2, batch, 128) -> (seq_len, batch, 2, 128) -> (seq_len, batch, 256)
        y_tr_t = self.new_name('gru_Y_tr')
        self.nodes.append(helper.make_node('Transpose', [y_t], [y_tr_t], name='gru_Y_tr', perm=[0, 2, 1, 3]))
        y_rs_t = self.new_name('gru_Y_rs')
        shape_t = self.new_name('gru_Y_shape')
        self.initializers.append(shape_init(shape_t, [0, 0, -1]))
        self.nodes.append(helper.make_node('Reshape', [y_tr_t, shape_t], [y_rs_t], name='gru_Y_reshape'))

        # Store result for the final reshape0 (which expects (seq_len, batch, 256))
        self.name_map['gru0_rnn0'] = y_rs_t
        return True


def convert(model_info):
    name = model_info['name']
    model_dir = model_info['dir']
    prefix_path = os.path.join(model_dir, model_info['prefix'])
    epoch = model_info['epoch']
    img_width = model_info['img_width']

    seq_len = img_width // 4
    hidden_dim = model_info['hidden'] * 2

    print(f"\n{'='*60}")
    print(f"Building ONNX model: {name}")

    sym, arg_params, aux_params = mx.model.load_checkpoint(prefix_path, epoch)
    print(f"  Loaded MXNet checkpoint (epoch {epoch})")

    pred_fc = sym.get_internals()['pred_fc_output']
    sym_dict = json.loads(pred_fc.tojson())

    builder = ONNXBuilder(name)
    model = builder.build(sym_dict, arg_params, aux_params, seq_len, hidden_dim, img_width)

    output_path = os.path.join(model_dir, 'model.onnx')
    onnx.save(model, output_path)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  SAVED: {output_path} ({size_kb:.1f} KB)")

    # Verify
    try:
        onnx.checker.check_model(model)
        print(f"  ONNX structural check: PASSED")
    except Exception as e:
        print(f"  ONNX structural check: FAILED - {e}")

    # Print graph summary
    ops = {}
    for n in model.graph.node:
        ops[n.op_type] = ops.get(n.op_type, 0) + 1
    print(f"  Ops ({len(ops)} types): {dict(sorted(ops.items()))}")
    return output_path


if __name__ == '__main__':
    print("ONNX Model Builder for ALAS cnocr Models")
    print(f"MXNet: {mx.__version__}, onnx: {onnx.__version__}")

    models = [
        {
            'name': 'azur_lane',
            'dir': './bin/cnocr_models/azur_lane',
            'prefix': 'cnocr-v1.2.0-densenet-lite-gru',
            'epoch': 15,
            'img_width': 280,
            'hidden': 128,
        },
        {
            'name': 'azur_lane_jp',
            'dir': './bin/cnocr_models/azur_lane_jp',
            'prefix': 'cnocr-v1.2.0-densenet-lite-gru',
            'epoch': 20,
            'img_width': 280,
            'hidden': 128,
        },
        {
            'name': 'cnocr',
            'dir': './bin/cnocr_models/cnocr',
            'prefix': 'cnocr-v1.2.0-densenet-lite-gru',
            'epoch': 39,
            'img_width': 280,
            'hidden': 128,
        },
        {
            'name': 'jp',
            'dir': './bin/cnocr_models/jp',
            'prefix': 'cnocr-v1.2.0-densenet-lite-gru',
            'epoch': 125,
            'img_width': 280,
            'hidden': 128,
        },
        {
            'name': 'tw',
            'dir': './bin/cnocr_models/tw',
            'prefix': 'cnocr-v1.2.0-densenet-lite-gru',
            'epoch': 63,
            'img_width': 280,
            'hidden': 128,
        },
    ]

    for m in models:
        convert(m)

    print(f"\nDone.")