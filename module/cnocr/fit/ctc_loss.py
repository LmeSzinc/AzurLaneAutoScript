import mxnet as mx


def _add_warp_ctc_loss(pred, seq_len, num_label, label):
    """Adds Symbol.contrib.ctc_loss on top of pred symbol and returns the resulting symbol"""
    label = mx.sym.Reshape(data=label, shape=(-1,))
    label = mx.sym.Cast(data=label, dtype="int32")
    return mx.sym.WarpCTC(
        data=pred, label=label, label_length=num_label, input_length=seq_len
    )


def _add_mxnet_ctc_loss(pred, seq_len, label):
    """Adds Symbol.WapCTC on top of pred symbol and returns the resulting symbol"""
    pred_ctc = mx.sym.Reshape(
        data=pred, shape=(-4, seq_len, -1, 0)
    )  # res: (seq_len, batch_size, num_classes)
    # print('pred_ctc', pred_ctc.infer_shape()[1])

    loss = mx.sym.contrib.ctc_loss(data=pred_ctc, label=label)
    ctc_loss = mx.sym.MakeLoss(loss)

    softmax_class = mx.symbol.SoftmaxActivation(data=pred)
    softmax_loss = mx.sym.MakeLoss(softmax_class)
    softmax_loss = mx.sym.BlockGrad(softmax_loss)
    return mx.sym.Group([softmax_loss, ctc_loss])


def add_ctc_loss(pred, seq_len, num_label, loss_type):
    """Adds CTC loss on top of pred symbol and returns the resulting symbol"""
    label = mx.sym.Variable("label")
    # label = mx.sym.Variable('label', shape=(128, 4))
    if loss_type == "warpctc":
        # print("Using WarpCTC Loss")
        sm = _add_warp_ctc_loss(pred, seq_len, num_label, label)
    else:
        # print("Using MXNet CTC Loss")
        assert loss_type == "ctc"
        sm = _add_mxnet_ctc_loss(pred, seq_len, label)
    return sm
