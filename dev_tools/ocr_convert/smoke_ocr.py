"""Smoke test for the onnxruntime OCR backend (Python 3.11 environment).

Usage:
    .venv/Scripts/python.exe dev_tools/ocr_convert/smoke_ocr.py
"""
import os
import sys
import time

import cv2
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)


def main():
    from module.ocr.al_ocr import AlOcr

    model = AlOcr(model_name='azur_lane', root=os.path.join(REPO_ROOT, 'bin', 'cnocr_models', 'azur_lane'),
                  name='azur_lane')

    # synthetic line image: white background, black digits
    img = np.full((32, 200), 255, dtype=np.uint8)
    cv2.putText(img, '123456', (5, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 0, 2)

    start = time.time()
    res = model.atomic_ocr_for_single_lines([img], cand_alphabet='0123456789')
    elapsed = time.time() - start
    print('single line result:', res, f'({elapsed * 1000:.1f} ms)')

    # batch of lines with different widths
    images = [np.full((32, w), 255, dtype=np.uint8) for w in (80, 200, 120)]
    for i, w in enumerate((80, 200, 120)):
        cv2.putText(images[i], f'123456'[:max(1, w // 25)], (5, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 0, 2)
    start = time.time()
    res = model.atomic_ocr_for_single_lines(images, cand_alphabet='0123456789')
    elapsed = time.time() - start
    print('batch result:', res, f'({elapsed * 1000:.1f} ms)')

    # cnocr model (large charset)
    model_cn = AlOcr(model_name='cnocr', root=os.path.join(REPO_ROOT, 'bin', 'cnocr_models', 'cnocr'),
                     name='cnocr')
    img2 = np.full((32, 240), 255, dtype=np.uint8)
    cv2.putText(img2, 'abcdef', (5, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 0, 2)
    start = time.time()
    res = model_cn.ocr_for_single_lines([img2])
    elapsed = time.time() - start
    print('cnocr model result:', res, f'({elapsed * 1000:.1f} ms)')

    print('SMOKE OK')


if __name__ == '__main__':
    main()

