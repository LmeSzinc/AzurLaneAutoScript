"""
Build ONNX models from Alas self-trained cnocr checkpoints (MXNet format).

This builder translates the mxnet symbol graph (symbol.json) node by node
into an ONNX graph with dynamic batch and width. The bidirectional GRU is
faithfully reproduced with the ONNX Scan operator, because mxnet's gluon GRU
implements the cuDNN variant of GRU which is NOT equivalent to the standard
ONNX GRU:

    mxnet (cuDNN variant), gate order in params: [r, i, n]:
        r_t = sigmoid(W_ir x + b_ir + W_hr h + b_hr)
        i_t = sigmoid(W_ii x + b_ii + W_hi h + b_hi)
        n_t = tanh(W_in x + b_in + r_t * (W_hn h + b_hn))
        h_t = (1 - i_t) * n_t + i_t * h_(t-1)

Usage:
    Run in the .venv-mxnet environment (Python 3.8, mxnet 1.6.0):
        python dev_tools/ocr_convert/build_onnx.py [model_name ...]

Output:
    bin/cnocr_models/<name>/<name>.onnx
        graph input:  'data'  (N, 1, 32, W) float32, dynamic N and W
        graph output: 'probs' (T*N, num_classes) float32, softmax probabilities
"""
import json as _json
import os
import sys

import mxnet as mx
import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BIN_ROOT = os.path.join(REPO_ROOT, 'bin', 'cnocr_models')

MODEL_PREFIX = 'cnocr-v1.2.0-densenet-lite-gru'

MODEL_EPOCHS = {
    'azur_lane': 15,
    'azur_lane_jp': 20,
    'cnocr': 39,
    'jp': 125,
    'tw': 63,
}

OPSET = 13

# Nodes of the original graph that are folded into an equivalent chain:
#   densenet0_reshape0 (0,-3,0) + expand_dims0 + dropout0 (identity)
#   + crnn0_squeeze0 + crnn0_transpose0
# == (B,C,H,W) -> Transpose(0,3,1,2) -> (B,W,C,H)
#             -> Reshape(0,-1,C*H)  -> (B,W,C*H)
#             -> Transpose(1,0,2)   -> (W,B,C*H)
FOLDED_NODES = {
    'densenet0_reshape0', 'densenet0_expand_dims0', 'dropout0_fwd',
    'crnn0_squeeze0', 'crnn0_transpose0',
}

# Parameter-flattening Reshape nodes of the GRU; weights are read directly
# from the checkpoint instead.
GRU_PARAM_RESHAPES = {
    'gru0_reshape0', 'gru0_reshape1', 'gru0_reshape2', 'gru0_reshape3',
    'gru0_reshape4', 'gru0_reshape5', 'gru0_reshape6', 'gru0_reshape7',
}

SKIPPED_NODES = {'_rnn_param_concat', 'CTCLoss', 'MakeLoss', 'BlockGrad', '_zeros', 'reshape1'}


class Builder:
    def __init__(self, sym, params):
        self.sym = sym
        self.params = params  # name -> mx.nd.NDArray
        self.graph = _json.loads(sym.tojson())
        self.nodes = self.graph['nodes']
        self.nodes_by_name = {n['name']: i for i, n in enumerate(self.nodes)}
        self.initializers = []
        self.onnx_nodes = []
        self.value_cache = {}

    # ---------- helpers ----------

    def value(self, node_index, slot=0):
        key = (node_index, slot)
        if key not in self.value_cache:
            node = self.nodes[node_index]
            if node['op'] == 'null' and not node.get('inputs'):
                # graph input ('data') or parameter (weights/bn stats)
                self.value_cache[key] = node['name']
            else:
                name = node['name']
                self.value_cache[key] = f'{name}_output' if slot == 0 else f'{name}_output{slot}'
        return self.value_cache[key]

    def resolve_input(self, inp):
        if isinstance(inp, list):
            return self.value(inp[0], inp[1] if len(inp) > 1 else 0)
        return str(inp)

    def add_initializer(self, name, array):
        self.initializers.append(numpy_helper.from_array(np.ascontiguousarray(array), name=name))

    def weight(self, name):
        return self.params[name].asnumpy()

    @staticmethod
    def parse_tuple(s):
        if s is None:
            return None
        return tuple(int(x) for x in s.strip('()').replace(' ', '').split(',') if x)

    # ---------- node converters ----------

    def _convert_Convolution(self, idx, node):
        attrs = node['attrs']
        data, weight = [self.resolve_input(i) for i in node['inputs'][:2]]
        kernel = self.parse_tuple(attrs['kernel'])
        stride = self.parse_tuple(attrs['stride'])
        pad = self.parse_tuple(attrs['pad'])
        dilate = self.parse_tuple(attrs.get('dilate', '(1, 1)'))
        groups = int(attrs.get('num_group', '1'))
        kw = {'kernel_shape': kernel, 'strides': stride, 'dilations': dilate, 'group': groups}
        if any(pad):
            kw['pads'] = list(pad) * 2
        inputs = [data, weight]
        if attrs.get('no_bias', 'False') != 'True':
            inputs.append(self.resolve_input(node['inputs'][2]))
        self.onnx_nodes.append(helper.make_node(
            'Conv', inputs, [self.value(idx, 0)], name=node['name'], **kw))

    def _convert_BatchNorm(self, idx, node):
        attrs = node['attrs']
        data, gamma, beta, mean, var = [self.resolve_input(i) for i in node['inputs'][:5]]
        eps = float(attrs.get('eps', '1e-5'))
        self.onnx_nodes.append(helper.make_node(
            'BatchNormalization', [data, gamma, beta, mean, var],
            [self.value(idx, 0)],
            name=node['name'], epsilon=eps))

    def _convert_Activation(self, idx, node):
        act = node['attrs']['act_type']
        op = {'relu': 'Relu', 'sigmoid': 'Sigmoid', 'tanh': 'Tanh'}.get(act)
        if op is None:
            raise RuntimeError(f'Unsupported activation {act!r}')
        self.onnx_nodes.append(helper.make_node(
            op, [self.resolve_input(node['inputs'][0])], [self.value(idx, 0)], name=node['name']))

    def _convert_Pooling(self, idx, node):
        attrs = node['attrs']
        data = self.resolve_input(node['inputs'][0])
        kernel = self.parse_tuple(attrs['kernel'])
        stride = self.parse_tuple(attrs.get('stride', attrs['kernel']))
        pad = self.parse_tuple(attrs.get('pad', '(0, 0)'))
        op = 'MaxPool' if attrs['pool_type'] == 'max' else 'AveragePool'
        kw = {'kernel_shape': kernel, 'strides': stride}
        if any(pad):
            kw['pads'] = list(pad) * 2
        self.onnx_nodes.append(helper.make_node(
            op, [data], [self.value(idx, 0)], name=node['name'], **kw))

    def _convert_Concat(self, idx, node):
        inputs = [self.resolve_input(i) for i in node['inputs']]
        self.onnx_nodes.append(helper.make_node(
            'Concat', inputs, [self.value(idx, 0)], name=node['name'], axis=int(node['attrs']['dim'])))

    def _convert_Reshape(self, idx, node):
        # Only 'reshape0' (-3,-2) reaches here; GRU param reshapes and the
        # folded densenet chain are handled by skip lists.
        gru_out_channels = self.weight('pred_fc_weight').shape[1]
        shape = np.array([-1, gru_out_channels], dtype=np.int64)
        self.add_initializer(f'{node["name"]}_shape', shape)
        self.onnx_nodes.append(helper.make_node(
            'Reshape', [self.resolve_input(node['inputs'][0]), f'{node["name"]}_shape'],
            [self.value(idx, 0)], name=node['name']))

    def _convert_FullyConnected(self, idx, node):
        data = self.resolve_input(node['inputs'][0])
        w = self.resolve_input(node['inputs'][1])
        b = self.resolve_input(node['inputs'][2])
        self.onnx_nodes.append(helper.make_node(
            'Gemm', [data, w, b], [self.value(idx, 0)], name=node['name'],
            alpha=1.0, beta=1.0, transB=1))

    # ---------- GRU via Scan ----------

    def _emit_gru_scan(self, rnn_idx, rnn_node, data_val):
        name = rnn_node['name']
        hidden = int(rnn_node['attrs']['state_size'])
        C = self.hidden_size  # densenet output channels (C*H folded): 512

        def gate_mats(prefix):
            i2h = self.weight(f'gru0_{prefix}_i2h_weight')  # (3*hidden, C)
            h2h = self.weight(f'gru0_{prefix}_h2h_weight')  # (3*hidden, hidden)
            i2h_b = self.weight(f'gru0_{prefix}_i2h_bias')
            h2h_b = self.weight(f'gru0_{prefix}_h2h_bias')
            # gate order in mxnet params: [r, i, n]
            return {
                'x': [i2h[h:h + hidden].T.copy() for h in (0, hidden, 2 * hidden)],
                'h': [h2h[h:h + hidden].T.copy() for h in (0, hidden, 2 * hidden)],
                'xb': [i2h_b[h:h + hidden].copy() for h in (0, hidden, 2 * hidden)],
                'hb': [h2h_b[h:h + hidden].copy() for h in (0, hidden, 2 * hidden)],
            }

        sub_inits = []
        weight_names = {}

        def add_w(tag, kind, arr):
            nm = f'{name}_w_{tag}_{kind}'
            weight_names[(tag, kind)] = nm
            sub_inits.append(numpy_helper.from_array(np.ascontiguousarray(arr), name=nm))

        for tag, mats in (('f', gate_mats('l0')), ('b', gate_mats('r0'))):
            for k, key in (('xr', ('x', 0)), ('xi', ('x', 1)), ('xn', ('x', 2)),
                           ('hr', ('h', 0)), ('hi', ('h', 1)), ('hn', ('h', 2))):
                add_w(tag, k, mats[key[0]][key[1]])
            for k, key in (('xbr', ('xb', 0)), ('xbi', ('xb', 1)), ('xbn', ('xb', 2)),
                           ('hbr', ('hb', 0)), ('hbi', ('hb', 1)), ('hbn', ('hb', 2))):
                add_w(tag, k, mats[key[0]][key[1]])

        body_nodes = []
        # body inputs: h_fwd, h_bwd, x_fwd_t, x_bwd_t
        state_names = ['h_fwd', 'h_bwd']
        scan_in_names = ['x_fwd_t', 'x_bwd_t']
        # body outputs: h_fwd', h_bwd', y_fwd, y_bwd
        # NOTE: scan outputs must have names distinct from the state outputs,
        # otherwise onnxruntime fails to propagate the loop state.
        h_fwd_new, h_bwd_new = 'h_fwd_new', 'h_bwd_new'
        y_fwd_out, y_bwd_out = 'y_fwd_out', 'y_bwd_out'

        for tag, x_t, h_t, h_new in (('f', 'x_fwd_t', 'h_fwd', h_fwd_new),
                                     ('b', 'x_bwd_t', 'h_bwd', h_bwd_new)):
            w = lambda k: weight_names[(tag, k)]
            out = f'{name}_{tag}_{{}}'
            xr, xi, xn = out.format('xr'), out.format('xi'), out.format('xn')
            body_nodes += [
                helper.make_node('MatMul', [x_t, w('xr')], [xr]),
                helper.make_node('MatMul', [x_t, w('xi')], [xi]),
                helper.make_node('MatMul', [x_t, w('xn')], [xn]),
            ]
            hr, hi, hn = out.format('hr'), out.format('hi'), out.format('hn')
            body_nodes += [
                helper.make_node('MatMul', [h_t, w('hr')], [hr]),
                helper.make_node('MatMul', [h_t, w('hi')], [hi]),
                helper.make_node('MatMul', [h_t, w('hn')], [hn]),
            ]
            r_sum, i_sum = out.format('r_sum'), out.format('i_sum')
            body_nodes += [
                helper.make_node('Add', [xr, w('xbr')], [out.format('xr_b')]),
                helper.make_node('Add', [hr, w('hbr')], [out.format('hr_b')]),
                helper.make_node('Add', [out.format('xr_b'), out.format('hr_b')], [r_sum]),
                helper.make_node('Add', [xi, w('xbi')], [out.format('xi_b')]),
                helper.make_node('Add', [hi, w('hbi')], [out.format('hi_b')]),
                helper.make_node('Add', [out.format('xi_b'), out.format('hi_b')], [i_sum]),
            ]
            rr, ii = out.format('r'), out.format('i')
            body_nodes += [
                helper.make_node('Sigmoid', [r_sum], [rr]),
                helper.make_node('Sigmoid', [i_sum], [ii]),
            ]
            # n = tanh(xn + xbn + r * (hn + hbn))
            n_sum = out.format('n_sum')
            body_nodes += [
                helper.make_node('Add', [hn, w('hbn')], [out.format('hn_b')]),
                helper.make_node('Mul', [rr, out.format('hn_b')], [out.format('r_hn')]),
                helper.make_node('Add', [xn, w('xbn')], [out.format('xn_b')]),
                helper.make_node('Add', [out.format('xn_b'), out.format('r_hn')], [n_sum]),
                helper.make_node('Tanh', [n_sum], [out.format('n')]),
            ]
            # h' = (1 - i) * n + i * h
            body_nodes += [
                helper.make_node('Constant', [], [out.format('one')],
                                 value=helper.make_tensor('one', TensorProto.FLOAT, [1], [1.0])),
                helper.make_node('Sub', [out.format('one'), ii], [out.format('one_minus_i')]),
                helper.make_node('Mul', [out.format('one_minus_i'), out.format('n')], [out.format('t1')]),
                helper.make_node('Mul', [ii, h_t], [out.format('t2')]),
                helper.make_node('Add', [out.format('t1'), out.format('t2')], [h_new]),
            ]

        body_nodes += [
            helper.make_node('Identity', [h_fwd_new], [y_fwd_out]),
            helper.make_node('Identity', [h_bwd_new], [y_bwd_out]),
        ]

        body = helper.make_graph(
            body_nodes, f'{name}_body',
            [helper.make_tensor_value_info('h_fwd', TensorProto.FLOAT, [None, hidden]),
             helper.make_tensor_value_info('h_bwd', TensorProto.FLOAT, [None, hidden]),
             helper.make_tensor_value_info('x_fwd_t', TensorProto.FLOAT, [None, C]),
             helper.make_tensor_value_info('x_bwd_t', TensorProto.FLOAT, [None, C])],
            [helper.make_tensor_value_info(h_fwd_new, TensorProto.FLOAT, [None, hidden]),
             helper.make_tensor_value_info(h_bwd_new, TensorProto.FLOAT, [None, hidden]),
             helper.make_tensor_value_info(y_fwd_out, TensorProto.FLOAT, [None, hidden]),
             helper.make_tensor_value_info(y_bwd_out, TensorProto.FLOAT, [None, hidden])],
            sub_inits,
        )

        # h0 zeros (N, hidden) in the main graph
        gather_idx = f'{name}_gather_idx'
        self.add_initializer(gather_idx, np.array([1], dtype=np.int64))
        hidden_const = f'{name}_hidden_const'
        self.add_initializer(hidden_const, np.array([hidden], dtype=np.int64))
        self.onnx_nodes += [
            helper.make_node('Shape', [data_val], [f'{name}_data_shape']),
            helper.make_node('Gather', [f'{name}_data_shape', gather_idx], [f'{name}_n_shape'], axis=0),
            helper.make_node('Concat', [f'{name}_n_shape', hidden_const], [f'{name}_h0_shape'], axis=0),
            helper.make_node('ConstantOfShape', [f'{name}_h0_shape'], [f'{name}_h0'],
                             value=helper.make_tensor('zero', TensorProto.FLOAT, [1], [0.0])),
        ]

        scan_outs = [f'{name}_state_f', f'{name}_state_b', f'{name}_yf', f'{name}_yb']
        self.onnx_nodes.append(helper.make_node(
            'Scan',
            [f'{name}_h0', f'{name}_h0', data_val, data_val],
            scan_outs,
            body=body,
            num_scan_inputs=2,
            scan_input_axes=[0, 0],
            scan_input_directions=[0, 1],
            scan_output_axes=[0, 0],
            name=name,
        ))
        # The backward scan output is in iteration order (T-1 -> 0); reverse it
        # back to the original time order to match mxnet's bidirectional output.
        seq_lens = f'{name}_seq_lens'
        # Scan input is (T, N, C): T is dim 0, N is dim 1.
        t_idx = f'{name}_t_idx'
        self.add_initializer(t_idx, np.array([0], dtype=np.int64))
        self.add_initializer(f'{name}_slice_starts', np.array([1], dtype=np.int64))
        self.add_initializer(f'{name}_slice_ends', np.array([2], dtype=np.int64))
        self.onnx_nodes += [
            helper.make_node('Shape', [data_val], [f'{name}_full_shape']),
            helper.make_node('Gather', [f'{name}_full_shape', t_idx], [f'{name}_t'], axis=0),
            helper.make_node('Slice', [f'{name}_full_shape', f'{name}_slice_starts', f'{name}_slice_ends'],
                             [f'{name}_n_vec']),
            helper.make_node('ConstantOfShape', [f'{name}_n_vec'], [f'{name}_ones'],
                             value=helper.make_tensor('one', TensorProto.INT64, [1], [1])),
            helper.make_node('Mul', [f'{name}_ones', f'{name}_t'], [seq_lens]),
            helper.make_node('ReverseSequence', [f'{name}_yb', seq_lens], [f'{name}_yb_rev'],
                             batch_axis=1, time_axis=0),
        ]
        self.onnx_nodes.append(helper.make_node(
            'Concat', [f'{name}_yf', f'{name}_yb_rev'], [self.value(rnn_idx, 0)],
            name=f'{name}_concat', axis=2))
        # second RNN output (state) is unused by the graph tail

    # ---------- main ----------

    def run(self, out_path):
        self.hidden_size = self.weight('pred_fc_weight').shape[1] * 2  # GRU input channels

        rnn_idx = self.nodes_by_name['gru0_rnn0']
        for idx, node in enumerate(self.nodes):
            op, name = node['op'], node['name']
            if op == 'null' or name == 'label':
                continue
            if op in SKIPPED_NODES or name in SKIPPED_NODES:
                continue
            if name in GRU_PARAM_RESHAPES or name == 'softmaxactivation0':
                continue
            if name in FOLDED_NODES:
                if name == 'densenet0_reshape0':
                    # Folded densenet chain: (B,C,H,W) -> (W,B,C*H)
                    pool_val = self.value(self.nodes_by_name['densenet0_stage3_pool0_fwd'])
                    t1, t2 = 'densenet0_chain_t1', 'densenet0_chain_t2'
                    shape_name = 'densenet0_chain_shape'
                    self.add_initializer(shape_name, np.array([0, -1, self.hidden_size], dtype=np.int64))
                    self.onnx_nodes += [
                        helper.make_node('Transpose', [pool_val], [t1], perm=[0, 3, 1, 2]),
                        helper.make_node('Reshape', [t1, shape_name], [t2]),
                        helper.make_node('Transpose', [t2], [self.value(self.nodes_by_name['crnn0_transpose0'])],
                                         perm=[1, 0, 2]),
                    ]
                continue
            if idx == rnn_idx:
                # GRU via Scan, emitted in topological position
                self._emit_gru_scan(rnn_idx, node,
                                    self.value(self.nodes_by_name['crnn0_transpose0']))
                continue
            handler = getattr(self, f'_convert_{op}', None)
            if handler is None:
                raise RuntimeError(f'No converter for op {op!r} at node {name!r}')
            handler(idx, node)

        # softmax of pred_fc output
        pred_val = self.value(self.nodes_by_name['pred_fc'])
        self.onnx_nodes.append(helper.make_node('Softmax', [pred_val], ['probs'], axis=-1))

        # initializers: add params referenced by emitted nodes
        used = set()
        for n in self.onnx_nodes:
            used.update(n.input)
            used.update(n.output)
        for pname, arr in self.params.items():
            if pname in used:
                self.add_initializer(pname, arr.asnumpy())

        graph_input = helper.make_tensor_value_info('data', TensorProto.FLOAT, ['N', 1, 32, 'W'])
        graph_output = helper.make_tensor_value_info('probs', TensorProto.FLOAT, [None, None])
        graph = helper.make_graph(self.onnx_nodes, 'alas_ocr', [graph_input], [graph_output], self.initializers)
        model = helper.make_model(graph, opset_imports=[helper.make_opsetid('', OPSET)])
        model.ir_version = 8
        onnx.checker.check_model(model)
        onnx.save(model, out_path)
        print(f'saved {out_path} ({len(self.onnx_nodes)} nodes)')


def main():
    names = sys.argv[1:] or list(MODEL_EPOCHS.keys())
    for name in names:
        model_dir = os.path.join(BIN_ROOT, name)
        prefix = os.path.join(model_dir, MODEL_PREFIX)
        sym, arg_params, aux_params = mx.model.load_checkpoint(prefix, MODEL_EPOCHS[name])
        params = {k: v for k, v in arg_params.items()}
        params.update(aux_params)
        builder = Builder(sym, params)
        builder.run(os.path.join(model_dir, f'{name}.onnx'))


if __name__ == '__main__':
    main()
