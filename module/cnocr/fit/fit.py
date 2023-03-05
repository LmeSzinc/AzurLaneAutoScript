import logging
import os
import mxnet as mx

from ..utils import gen_context


def _load_model(args):
    if "load_epoch" not in args or args.load_epoch is None:
        return None, None, None
    assert args.prefix is not None
    model_prefix = args.prefix
    sym, arg_params, aux_params = mx.model.load_checkpoint(
        model_prefix, args.load_epoch
    )
    logging.info("Loaded model %s-%04d.params", model_prefix, args.load_epoch)
    return sym, arg_params, aux_params


def fit(network, data_train, data_val, metrics, args, hp, data_names=None):
    context = gen_context(args.gpu)
    logging.info("hp: %s", hp)

    sym, arg_params, aux_params = _load_model(args)
    # if sym is not None:
    #     assert sym.tojson() == network.tojson()
    if not os.path.exists(os.path.dirname(args.prefix)):
        os.makedirs(os.path.dirname(args.prefix))

    module = mx.mod.Module(
        symbol=network,
        data_names=["data"] if data_names is None else data_names,
        label_names=["label"],
        context=context,
    )

    begin_epoch = args.load_epoch if args.load_epoch else 0
    num_epoch = hp.num_epoch + begin_epoch

    optimizer_params = {
        "learning_rate": hp.learning_rate,
        # 'momentum': hp.momentum,
        "wd": hp.wd,
    }
    if hp.clip_gradient is not None:
        optimizer_params["clip_gradient"] = hp.clip_gradient

    module.fit(
        train_data=data_train,
        eval_data=data_val,
        begin_epoch=begin_epoch,
        num_epoch=num_epoch,
        # use metrics.accuracy or metrics.accuracy_lcs
        eval_metric=mx.metric.np(metrics.accuracy, allow_extra_outputs=True),
        optimizer=hp.optimizer,
        optimizer_params=optimizer_params,
        initializer=mx.init.Xavier(factor_type="in", magnitude=2.34),
        arg_params=arg_params,
        aux_params=aux_params,
        batch_end_callback=mx.callback.Speedometer(hp.batch_size, 50),
        epoch_end_callback=mx.callback.do_checkpoint(args.prefix),
    )
