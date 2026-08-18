"""
Compare inference outputs between the original mxnet model and the
converted ONNX model, element by element.

Usage:
    Run in the .venv-mxnet environment (Python 3.8):
        python dev_tools/ocr_convert/compare_mxnet_onnx.py [model_name]
"""

import os
import sys

import cv2
import mxnet as mx
import numpy as np
import onnxruntime as ort
from cnocr.cn_ocr import gen_network, load_module
from cnocr.hyperparams.cn_hyperparams import CnHyperparams

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BIN_ROOT = os.path.join(REPO_ROOT, "bin", "cnocr_models")

MODEL_PREFIX = "cnocr-v1.2.0-densenet-lite-gru"
MODEL_EPOCHS = {
    "azur_lane": 15,
    "azur_lane_jp": 20,
    "cnocr": 39,
    "jp": 125,
    "tw": 63,
}


def make_test_images():
    """Synthetic line images, preprocessed to (H, W) uint8, black text on white."""
    images = []
    widths = [280, 200, 333]
    for w in widths:
        img = np.full((32, w), 255, dtype=np.uint8)
        cv2.putText(img, "123456", (5, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 0, 2)
        images.append(img)
    rng = np.random.default_rng(0)
    for w in widths:
        images.append((rng.random((32, w)) * 255).astype(np.uint8))
    return images


def build_mxnet_module(model_name):
    model_dir = os.path.join(BIN_ROOT, model_name)
    prefix = os.path.join(model_dir, MODEL_PREFIX)
    epoch = MODEL_EPOCHS[model_name]
    hp = CnHyperparams()
    hp._loss_type = None
    hp._num_classes = load_num_classes(model_name)
    network, hp = gen_network("densenet-lite-gru", hp, model_name)
    data_names = ["data"]
    data_shapes = [(data_names[0], (1, 1, hp.img_height, hp.img_width))]
    mod = load_module(
        prefix,
        epoch,
        data_names,
        data_shapes,
        network=network,
        net_prefix=model_name,
        context="cpu",
    )
    return mod


def load_num_classes(model_name):
    import os

    with open(os.path.join(BIN_ROOT, model_name, "label_cn.txt"), encoding="utf-8") as f:
        return len(f.read().splitlines()) + 1  # +1 for blank


def mxnet_infer(mod, images):
    """images: list of (32, W) uint8 -> list of (T, 1, C) float arrays"""
    outs = []
    for img in images:
        new_w = int(round(32 / img.shape[0] * img.shape[1]))
        img = cv2.resize(img, (new_w, 32))
        x = np.expand_dims(img, 0).astype("float32") / 255.0
        x = x[None, :]  # (1, 1, 32, W)
        prob = mod.predict(mx.nd.array(x))
        prob = prob.asnumpy()
        batch = 1
        prob = np.reshape(prob, (-1, batch, prob.shape[1]))
        outs.append(prob)
    return outs


def onnx_infer(session, images):
    outs = []
    for img in images:
        new_w = int(round(32 / img.shape[0] * img.shape[1]))
        img = cv2.resize(img, (new_w, 32))
        x = np.expand_dims(img, 0).astype("float32") / 255.0
        x = x[None, :]  # (1, 1, 32, W)
        prob = session.run(["probs"], {"data": x})[0]
        prob = np.reshape(prob, (-1, 1, prob.shape[1]))
        outs.append(prob)
    return outs


def main():
    model_name = sys.argv[1] if len(sys.argv) > 1 else "azur_lane"
    onnx_path = os.path.join(BIN_ROOT, model_name, f"{model_name}.onnx")
    if not os.path.exists(onnx_path):
        raise FileNotFoundError(onnx_path)

    mod = build_mxnet_module(model_name)
    sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    print(f"onnx input: {[i.shape for i in sess.get_inputs()]}")
    print(f"onnx output: {[o.shape for o in sess.get_outputs()]}")

    images = make_test_images()
    mx_outs = mxnet_infer(mod, images)
    on_outs = onnx_infer(sess, images)

    all_ok = True
    for i, (a, b) in enumerate(zip(mx_outs, on_outs)):
        ok = a.shape == b.shape and np.allclose(a, b, atol=1e-3, rtol=1e-3)
        max_diff = float(np.abs(a - b).max()) if a.shape == b.shape else float("inf")
        argmax_same = a.shape == b.shape and bool((a.argmax(-1) == b.argmax(-1)).all())
        print(
            f"image {i}: shape mx={a.shape} onnx={b.shape} allclose={ok} "
            f"max_diff={max_diff:.3e} argmax_same={argmax_same}"
        )
        all_ok = all_ok and ok and argmax_same

    if all_ok:
        print("ALL MATCH")
        return 0
    print("MISMATCH FOUND")
    return 1


if __name__ == "__main__":
    sys.exit(main())
