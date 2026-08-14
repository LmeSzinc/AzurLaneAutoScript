"""Verify batched inference (ocr_for_single_lines path) matches mxnet."""
import os

import cv2
import mxnet as mx
import numpy as np
import onnxruntime as ort

from cnocr.cn_ocr import gen_network, load_module
from cnocr.hyperparams.cn_hyperparams import CnHyperparams

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BIN_ROOT = os.path.join(REPO_ROOT, 'bin', 'cnocr_models')
PREFIX = os.path.join(BIN_ROOT, 'azur_lane', 'cnocr-v1.2.0-densenet-lite-gru')


def main():
    hp = CnHyperparams()
    hp._loss_type = None
    hp._num_classes = 39
    network, hp = gen_network('densenet-lite-gru', hp, 'azur_lane')
    mod = load_module(PREFIX, 15, ['data'], [('data', (3, 1, hp.img_height, hp.img_width))],
                      network=network, net_prefix='azur_lane', context='cpu')

    # batch of 3 images with different widths, padded to the max width
    rng = np.random.default_rng(7)
    widths = [160, 280, 200]
    max_w = max(widths)
    batch = np.zeros((3, 1, 32, max_w), dtype='float32')
    for i, w in enumerate(widths):
        img = (rng.random((32, w)) * 255).astype(np.uint8)
        batch[i, 0, :, :w] = img / 255.0
    img_widths = widths

    prob_mx = mod.predict(mx.nd.array(batch)).asnumpy()  # (T*N, C)
    prob_mx = np.reshape(prob_mx, (-1, 3, prob_mx.shape[1]))

    sess = ort.InferenceSession(os.path.join(BIN_ROOT, 'azur_lane', 'azur_lane.onnx'),
                                providers=['CPUExecutionProvider'])
    prob_on = sess.run(['probs'], {'data': batch})[0]
    prob_on = np.reshape(prob_on, (-1, 3, prob_on.shape[1]))

    print('mx shape:', prob_mx.shape, 'onnx shape:', prob_on.shape)
    print('max diff:', np.abs(prob_mx - prob_on).max())
    print('argmax same:', bool((prob_mx.argmax(-1) == prob_on.argmax(-1)).all()))
    print('per-image rows (mx vs onnx):',
          [prob_mx.shape[0], prob_on.shape[0]])


if __name__ == '__main__':
    main()
