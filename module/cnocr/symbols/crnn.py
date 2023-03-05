# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
LeCun, Yann, Leon Bottou, Yoshua Bengio, and Patrick Haffner.
Gradient-based learning applied to document recognition.
Proceedings of the IEEE (1998)
"""
from copy import deepcopy
import mxnet as mx
from mxnet.gluon import nn
from mxnet.gluon.rnn.rnn_layer import LSTM, GRU

from .densenet import DenseNet
from ..fit.ctc_loss import add_ctc_loss


def gen_network(model_name, hp, net_prefix=None):
    hp = deepcopy(hp)
    hp.seq_model_type = model_name.rsplit("-", maxsplit=1)[-1]
    model_name = model_name.lower()
    if model_name.startswith("densenet"):
        hp.seq_len_cmpr_ratio = 4
        layer_channels = (
            (32, 64, 128, 256)
            if model_name.startswith("densenet-lite")
            else (64, 128, 256, 512)
        )
        shorter = model_name.startswith("densenet-s-") or model_name.startswith(
            "densenet-lite-s-"
        )
        seq_len = hp.img_width // 8 if shorter else hp.img_width // 4
        hp.set_seq_length(seq_len)
        densenet = DenseNet(layer_channels, shorter=shorter, prefix=net_prefix)
        densenet.hybridize()
        model = CRnn(hp, densenet, prefix=net_prefix)
    elif model_name.startswith("conv-lite"):
        hp.seq_len_cmpr_ratio = 4
        shorter = model_name.startswith("conv-lite-s-")
        seq_len = hp.img_width // 8 if shorter else hp.img_width // 4 - 1
        hp.set_seq_length(seq_len)

        def model(data):
            with mx.name.Prefix(net_prefix or ""):
                return crnn_lstm_lite(hp, data, shorter=shorter)

    elif model_name.startswith("conv"):
        hp.seq_len_cmpr_ratio = 8
        hp.set_seq_length(hp.img_width // 8)

        def model(data):
            with mx.name.Prefix(net_prefix or ""):
                return crnn_lstm(hp, data)

    else:
        raise NotImplementedError("bad model_name: %s", model_name)

    return pipline(model, hp, net_prefix=net_prefix), hp


def get_infer_shape(sym_model, hp):
    init_states = {
        "data": (hp.batch_size, 1, hp.img_height, hp.img_width),
        "label": (hp.batch_size, hp.num_label),
    }
    internals = sym_model.get_internals()
    _, out_shapes, _ = internals.infer_shape(**init_states)
    shape_dict = dict(zip(internals.list_outputs(), out_shapes))
    return shape_dict


def gen_seq_model(hp, **kw):
    if hp.seq_model_type.lower() == "lstm":
        seq_model = LSTM(hp.num_hidden, hp.num_lstm_layer, bidirectional=True, **kw)
    elif hp.seq_model_type.lower() == "gru":
        seq_model = GRU(hp.num_hidden, hp.num_lstm_layer, bidirectional=True, **kw)
    else:

        def fc_seq_model(data):
            if kw.get("prefix", None):
                with mx.name.Prefix(kw["prefix"]):
                    fc = mx.sym.FullyConnected(
                        data, num_hidden=hp.num_hidden, flatten=False, name="seq-fc"
                    )
                    net = mx.sym.Activation(data=fc, act_type="relu", name="seq-relu")
            else:
                fc = mx.sym.FullyConnected(
                    data, num_hidden=hp.num_hidden, flatten=False, name="seq-fc"
                )
                net = mx.sym.Activation(data=fc, act_type="relu", name="seq-relu")
            return net

        seq_model = fc_seq_model
    return seq_model


class CRnn(nn.HybridBlock):
    def __init__(self, hp, emb_model, **kw):
        super().__init__(**kw)
        self.hp = hp
        self.emb_model = emb_model
        self.dropout = nn.Dropout(hp.dropout)

        self.seq_model = gen_seq_model(hp, **kw)

    def hybrid_forward(self, F, X):
        embs = self.emb_model(X)  # res: bz x emb_size x 1 x seq_len
        hp = self.hp
        if hp.dropout > 0:
            embs = self.dropout(embs)

        embs = F.squeeze(embs, axis=2)  # res: bz x emb_size x seq_len
        embs = F.transpose(embs, axes=(2, 0, 1))  # res: seq_len x bz x emb_size
        # res: `(sequence_length, batch_size, 2*num_hidden)`
        return self.seq_model(embs)


def pipline(model, hp, data=None, *, net_prefix=""):
    # 构建用于训练的整个计算图
    data = data if data is not None else mx.sym.Variable("data")

    output = model(data)
    if net_prefix:
        with mx.name.Prefix(net_prefix):
            output = mx.symbol.reshape(output, shape=(-3, -2))  # res: (seq_len * bz, c)
            pred = mx.sym.FullyConnected(
                data=output, num_hidden=hp.num_classes, name="pred_fc"
            )  # (bz x 35) x num_classes
    else:
        output = mx.symbol.reshape(output, shape=(-3, -2))  # res: (seq_len * bz, c)
        pred = mx.sym.FullyConnected(
            data=output, num_hidden=hp.num_classes, name="pred_fc"
        )  # (bz x 35) x num_classes
    # print('pred', pred.infer_shape()[1])
    # import pdb; pdb.set_trace()

    if hp.loss_type:
        # Training mode, add loss
        return add_ctc_loss(pred, hp.seq_length, hp.num_label, hp.loss_type)
    else:
        # Inference mode, add softmax
        return mx.sym.softmax(data=pred, name="softmax")


def convRelu(i, input_data, kernel_size, layer_size, padding_size, bn=True):
    layer = mx.symbol.Convolution(
        name="conv-%d" % i,
        data=input_data,
        kernel=kernel_size,
        pad=padding_size,
        num_filter=layer_size,
    )
    # in_channel = input_data.infer_shape()[1][0][1]
    # num_params = in_channel * kernel_size[0] * kernel_size[1] * layer_size
    # print('number of conv-%d layer parameters: %d' % (i, num_params))
    if bn:
        layer = mx.sym.BatchNorm(data=layer, name="batchnorm-%d" % i)
    layer = mx.sym.LeakyReLU(data=layer, name="leakyrelu-%d" % i)
    # layer = mx.symbol.Convolution(name='conv-%d-1x1' % i, data=layer, kernel=(1, 1), pad=(0, 0),
    #                               num_filter=layer_size[i])
    # if bn:
    #     layer = mx.sym.BatchNorm(data=layer, name='batchnorm-%d-1x1' % i)
    # layer = mx.sym.LeakyReLU(data=layer, name='leakyrelu-%d-1x1' % i)
    return layer


def bottle_conv(i, input_data, kernel_size, layer_size, padding_size, bn=True):
    bottle_channel = layer_size // 2
    layer = mx.symbol.Convolution(
        name="conv-%d-1-1x1" % i,
        data=input_data,
        kernel=(1, 1),
        pad=(0, 0),
        num_filter=bottle_channel,
    )
    layer = mx.sym.LeakyReLU(data=layer, name="leakyrelu-%d-1" % i)
    layer = mx.symbol.Convolution(
        name="conv-%d" % i,
        data=layer,
        kernel=kernel_size,
        pad=padding_size,
        num_filter=bottle_channel,
    )
    layer = mx.sym.LeakyReLU(data=layer, name="leakyrelu-%d-2" % i)
    layer = mx.symbol.Convolution(
        name="conv-%d-2-1x1" % i,
        data=layer,
        kernel=(1, 1),
        pad=(0, 0),
        num_filter=layer_size,
    )
    # in_channel = input_data.infer_shape()[1][0][1]
    # num_params = in_channel * bottle_channel
    # num_params += bottle_channel * kernel_size[0] * kernel_size[1] * bottle_channel
    # num_params += bottle_channel * layer_size
    # print('number of bottle-conv-%d layer parameters: %d' % (i, num_params))
    if bn:
        layer = mx.sym.BatchNorm(data=layer, name="batchnorm-%d" % i)
    layer = mx.sym.LeakyReLU(data=layer, name="leakyrelu-%d" % i)
    return layer


def crnn_lstm(hp, data):
    kernel_size = [(3, 3), (3, 3), (3, 3), (3, 3), (3, 3), (3, 3)]
    padding_size = [(1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1)]
    layer_size = [min(32 * 2 ** (i + 1), 512) for i in range(len(kernel_size))]

    def convRelu(i, input_data, bn=True):
        layer = mx.symbol.Convolution(
            name="conv-%d" % i,
            data=input_data,
            kernel=kernel_size[i],
            pad=padding_size[i],
            num_filter=layer_size[i],
        )
        if bn:
            layer = mx.sym.BatchNorm(data=layer, name="batchnorm-%d" % i)
        layer = mx.sym.LeakyReLU(data=layer, name="leakyrelu-%d" % i)
        layer = mx.symbol.Convolution(
            name="conv-%d-1x1" % i,
            data=layer,
            kernel=(1, 1),
            pad=(0, 0),
            num_filter=layer_size[i],
        )
        if bn:
            layer = mx.sym.BatchNorm(data=layer, name="batchnorm-%d-1x1" % i)
        layer = mx.sym.LeakyReLU(data=layer, name="leakyrelu-%d-1x1" % i)
        return layer

    net = convRelu(0, data)  # bz x f x 32 x 280
    # print('0', net.infer_shape()[1])
    max = mx.sym.Pooling(
        data=net, name="pool-0_m", pool_type="max", kernel=(2, 2), stride=(2, 2)
    )
    avg = mx.sym.Pooling(
        data=net, name="pool-0_a", pool_type="avg", kernel=(2, 2), stride=(2, 2)
    )
    net = max - avg  # 8 x 70
    net = convRelu(1, net)
    # print('2', net.infer_shape()[1])
    net = mx.sym.Pooling(
        data=net, name="pool-1", pool_type="max", kernel=(2, 2), stride=(2, 2)
    )  # res: bz x f x 8 x 70
    # print('3', net.infer_shape()[1])
    net = convRelu(2, net, True)
    net = convRelu(3, net)
    net = mx.sym.Pooling(
        data=net, name="pool-2", pool_type="max", kernel=(2, 2), stride=(2, 2)
    )  # res: bz x f x 4 x 35
    # print('4', net.infer_shape()[1])
    net = convRelu(4, net, True)
    net = convRelu(5, net)
    net = mx.symbol.Pooling(
        data=net, kernel=(4, 1), pool_type="avg", name="pool1"
    )  # res: bz x f x 1 x 35
    # print('5', net.infer_shape()[1])

    if hp.dropout > 0:
        net = mx.symbol.Dropout(data=net, p=hp.dropout)

    net = mx.symbol.squeeze(net, axis=2)  # res: bz x emb_size x seq_len
    net = mx.symbol.transpose(net, axes=(2, 0, 1))

    seq_model = gen_seq_model(hp)
    hidden_concat = seq_model(net)

    return hidden_concat


def crnn_lstm_lite(hp, data, *, shorter=False):
    kernel_size = [(3, 3), (3, 3), (3, 3), (3, 3), (3, 3), (3, 3)]
    padding_size = [(1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1)]
    layer_size = [min(32 * 2 ** (i + 1), 512) for i in range(len(kernel_size))]

    net = convRelu(
        0, data, kernel_size[0], layer_size[0], padding_size[0]
    )  # bz x 64 x 32 x 280
    # print('0', net.infer_shape()[1])
    net = convRelu(
        1, net, kernel_size[1], layer_size[1], padding_size[1], True
    )  # bz x 128 x 16 x 140
    # print('1', net.infer_shape()[1])
    net = mx.sym.Pooling(
        data=net, name="pool-0", pool_type="max", kernel=(2, 2), stride=(2, 2)
    )
    # avg = mx.sym.Pooling(data=net, name='pool-0_a', pool_type='avg', kernel=(2, 2), stride=(2, 2))
    # net = max - avg  # bz x 64 x 16 x 140
    # print('2', net.infer_shape()[1])
    # res: bz x 128 x 8 x 70
    # net = mx.sym.Pooling(data=net, name='pool-1', pool_type='max', kernel=(2, 2), stride=(2, 2))
    net = convRelu(
        2, net, kernel_size[2], layer_size[2], padding_size[2]
    )  # res: bz x 256 x 8 x 70
    # print('3', net.infer_shape()[1])
    net = convRelu(
        3, net, kernel_size[3], layer_size[3], padding_size[3], True
    )  # res: bz x 512 x 8 x 70
    # res: bz x 512 x 4 x 35
    x = net = mx.sym.Pooling(
        data=net, name="pool-1", pool_type="max", kernel=(2, 2), stride=(2, 2)
    )
    # print('4', net.infer_shape()[1])
    net = bottle_conv(4, net, kernel_size[4], layer_size[4], padding_size[4])
    net = bottle_conv(5, net, kernel_size[5], layer_size[5], padding_size[5], True) + x
    width_stride = 2 if shorter else 1
    # res: bz x 512 x 4 x 69 or bz x 512 x 4 x 35
    #  长度从70变成69的原因是pooling后没用padding
    net = mx.symbol.Pooling(
        data=net,
        name="pool-2",
        pool_type="max",
        kernel=(2, 2),
        stride=(2, width_stride),
    )
    # print('5', net.infer_shape()[1])
    # net = mx.symbol.Convolution(name='conv-%d' % 6, data=net, kernel=(4, 1), num_filter=layer_size[5])
    net = bottle_conv(6, net, (4, 1), layer_size[5], (0, 0))
    # print('6', net.infer_shape()[1])
    # num_params = layer_size[5] * 4 * 1 * layer_size[5]
    # print('number of conv-%d layer parameters: %d' % (6, num_params))

    if hp.dropout > 0:
        net = mx.symbol.Dropout(data=net, p=hp.dropout)

    net = mx.symbol.squeeze(net, axis=2)  # res: bz x emb_size x seq_len
    net = mx.symbol.transpose(net, axes=(2, 0, 1))

    seq_model = gen_seq_model(hp)
    hidden_concat = seq_model(net)

    # print('sequence length:', hp.seq_length)
    return hidden_concat
