"""Test the business-level Ocr wrapper (full import chain, Python 3.11)."""

import os
import sys

import cv2
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)
os.chdir(REPO_ROOT)


def main():
    from module.ocr.ocr import Digit, Ocr

    # color image, white text on dark background (like in-game UI)
    img = np.zeros((40, 200, 3), dtype=np.uint8)
    cv2.putText(img, "12345", (5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    ocr = Digit(
        buttons=(0, 0, 200, 40),
        lang="azur_lane",
        letter=(255, 255, 255),
        threshold=128,
        alphabet="0123456789IDSB",
        name="TEST",
    )
    result = ocr.ocr(img)
    print("Digit result:", result)

    # OcrYuv variant
    from module.ocr.ocr import DigitYuv

    ocr2 = DigitYuv(
        buttons=(0, 0, 200, 40),
        lang="azur_lane",
        letter=(255, 255, 255),
        threshold=128,
        alphabet="0123456789IDSB",
        name="TESTYUV",
    )
    result2 = ocr2.ocr(img)
    print("DigitYuv result:", result2)

    # multi-button Ocr
    ocr3 = Ocr(
        buttons=[(0, 0, 100, 40), (100, 0, 200, 40)],
        lang="azur_lane",
        letter=(255, 255, 255),
        threshold=128,
        alphabet="0123456789",
        name="MULTI",
    )
    result3 = ocr3.ocr(img)
    print("Multi-button result:", result3)

    print("BUSINESS CHAIN OK")


if __name__ == "__main__":
    main()
