from __future__ import print_function

from collections import namedtuple
import mxnet as mx
from mxnet.gluon.rnn.rnn_layer import LSTM

LSTMState = namedtuple("LSTMState", ["c", "h"])
LSTMParam = namedtuple(
    "LSTMParam", ["i2h_weight", "i2h_bias", "h2h_weight", "h2h_bias"]
)
LSTMModel = namedtuple(
    "LSTMModel",
    [
        "rnn_exec",
        "symbol",
        "init_states",
        "last_states",
        "forward_state",
        "backward_state",
        "seq_data",
        "seq_labels",
        "seq_outputs",
        "param_blocks",
    ],
)


def init_states(batch_size, num_lstm_layer, num_hidden):
    """
    Returns name and shape of init states of LSTM network

    Parameters
    ----------
    batch_size: list of tuple of str and tuple of int and int
    num_lstm_layer: int
    num_hidden: int

    Returns
    -------
    list of tuple of str and tuple of int and int
    """
    init_c = [
        ("l%d_init_c" % l, (batch_size, num_hidden)) for l in range(num_lstm_layer * 2)
    ]
    init_h = [
        ("l%d_init_h" % l, (batch_size, num_hidden)) for l in range(num_lstm_layer * 2)
    ]
    return init_c + init_h


def _lstm(num_hidden, indata, prev_state, param, seqidx, layeridx):
    """LSTM Cell symbol"""
    i2h = mx.sym.FullyConnected(
        data=indata,
        weight=param.i2h_weight,
        bias=param.i2h_bias,
        num_hidden=num_hidden * 4,
        name="t%d_l%d_i2h" % (seqidx, layeridx),
    )
    h2h = mx.sym.FullyConnected(
        data=prev_state.h,
        weight=param.h2h_weight,
        bias=param.h2h_bias,
        num_hidden=num_hidden * 4,
        name="t%d_l%d_h2h" % (seqidx, layeridx),
    )
    gates = i2h + h2h
    slice_gates = mx.sym.split(
        gates, num_outputs=4, name="t%d_l%d_slice" % (seqidx, layeridx)
    )
    in_gate = mx.sym.Activation(slice_gates[0], act_type="sigmoid")
    in_transform = mx.sym.Activation(slice_gates[1], act_type="tanh")
    forget_gate = mx.sym.Activation(slice_gates[2], act_type="sigmoid")
    out_gate = mx.sym.Activation(slice_gates[3], act_type="sigmoid")
    next_c = (forget_gate * prev_state.c) + (in_gate * in_transform)
    next_h = out_gate * mx.sym.Activation(next_c, act_type="tanh")
    return LSTMState(c=next_c, h=next_h)


def lstm2(net, num_lstm_layer, num_hidden):
    net = mx.symbol.squeeze(net, axis=2)  # res: bz x f x 35
    net = mx.symbol.transpose(net, axes=(2, 0, 1))
    # print('6', net.infer_shape()[1])

    lstm = LSTM(num_hidden, num_lstm_layer, bidirectional=True)
    # import pdb; pdb.set_trace()
    output = lstm(net)  # res: `(sequence_length, batch_size, 2*num_hidden)`
    # print('7', output.infer_shape()[1])
    return output
    # return mx.symbol.reshape(output, shape=(-3, -2))  # res: (bz * 35, c)
    # - **out**: output tensor with shape `(sequence_length, batch_size, num_hidden)`
    # when `layout` is "TNC". If `bidirectional` is True, output shape will instead
    # be `(sequence_length, batch_size, 2*num_hidden)`


def lstm(net, num_lstm_layer, num_hidden, seq_length):
    last_states = []
    forward_param = []
    backward_param = []

    # seq_length = mx.sym.Variable("seq_length")
    for i in range(num_lstm_layer * 2):
        last_states.append(
            LSTMState(
                c=mx.sym.Variable("l%d_init_c" % i), h=mx.sym.Variable("l%d_init_h" % i)
            )
        )
        if i % 2 == 0:
            forward_param.append(
                LSTMParam(
                    i2h_weight=mx.sym.Variable("l%d_i2h_weight" % i),
                    i2h_bias=mx.sym.Variable("l%d_i2h_bias" % i),
                    h2h_weight=mx.sym.Variable("l%d_h2h_weight" % i),
                    h2h_bias=mx.sym.Variable("l%d_h2h_bias" % i),
                )
            )
        else:
            backward_param.append(
                LSTMParam(
                    i2h_weight=mx.sym.Variable("l%d_i2h_weight" % i),
                    i2h_bias=mx.sym.Variable("l%d_i2h_bias" % i),
                    h2h_weight=mx.sym.Variable("l%d_h2h_weight" % i),
                    h2h_bias=mx.sym.Variable("l%d_h2h_bias" % i),
                )
            )

    slices_net = mx.sym.split(
        data=net, axis=3, num_outputs=seq_length, squeeze_axis=1
    )  # bz x features x 1 x time_step
    # slices_net = mx.sym.slice_axis(data=net, axis=3, begin=0, end=None)  # bz x features x 1 x time_step
    # seq_length = len(slices_net)

    forward_hidden = []
    for seqidx in range(seq_length):
        hidden = mx.sym.flatten(data=slices_net[seqidx])
        for i in range(num_lstm_layer):
            next_state = _lstm(
                num_hidden,
                indata=hidden,
                prev_state=last_states[2 * i],
                param=forward_param[i],
                seqidx=seqidx,
                layeridx=i,
            )
            hidden = next_state.h
            last_states[2 * i] = next_state
        forward_hidden.append(hidden)

    backward_hidden = []
    for seqidx in range(seq_length):
        k = seq_length - seqidx - 1
        hidden = mx.sym.flatten(data=slices_net[k])
        for i in range(num_lstm_layer):
            next_state = _lstm(
                num_hidden,
                indata=hidden,
                prev_state=last_states[2 * i + 1],
                param=backward_param[i],
                seqidx=k,
                layeridx=i,
            )
            hidden = next_state.h
            last_states[2 * i + 1] = next_state
        backward_hidden.insert(0, hidden)

    hidden_all = []
    for i in range(seq_length):
        hidden_all.append(
            mx.sym.concat(*[forward_hidden[i], backward_hidden[i]], dim=1)
        )

    hidden_concat = mx.sym.concat(*hidden_all, dim=0)
    return hidden_concat
