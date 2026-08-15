"""Test the socket-based OCR RPC server and client (Python 3.11)."""

import os
import sys
import time

import cv2
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)


def main():
    from module.ocr.rpc import ModelProxy, start_ocr_server_process, stop_ocr_server_process

    img = np.full((32, 200), 255, dtype=np.uint8)
    cv2.putText(img, "123456", (5, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 0, 2)

    start_ocr_server_process(port=22268)
    time.sleep(2)

    ModelProxy.init(address="127.0.0.1:22268")
    proxy = ModelProxy(lang="azur_lane")
    res = proxy.atomic_ocr_for_single_lines([img], "0123456789")
    print("rpc single lines:", res)

    res = proxy.ocr_for_single_line(img)
    print("rpc single line:", res)

    res = proxy.atomic_ocr(img, "0123456789")
    print("rpc ocr:", res)

    ModelProxy.close()
    stop_ocr_server_process()
    print("RPC OK")


if __name__ == "__main__":
    main()
