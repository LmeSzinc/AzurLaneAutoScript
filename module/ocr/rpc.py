import argparse
import multiprocessing
import pickle
from typing import List

import numpy as np
import zerorpc
import zmq

from module.webui.setting import State
from module.logger import logger

process: multiprocessing.Process = None


class ModelProxy:
    client: zerorpc.Client = None
    online = True

    @classmethod
    def init(cls, address="127.0.0.1:22268"):
        cls.client = zerorpc.Client(timeout=5)
        cls.client.connect(f"tcp://{address}")
        try:
            logger.info(f"Connecting to OCR server {address}")
            cls.client.hello()
            logger.info("Successfully connected to OCR server")
        except:
            cls.online = False
            logger.warning("Ocr server not running")

    def __init__(self, lang) -> None:
        self.lang = lang

    def ocr(self, img_fp: np.ndarray):
        if self.online:
            img_str = img_fp.dumps()
            try:
                return self.client("ocr", self.lang, img_str)
            except:
                self.online = False
        from module.ocr.models import OCR_MODEL
        return OCR_MODEL.__getattribute__(self.lang).ocr(img_fp)

    def ocr_for_single_line(self, img_fp: np.ndarray):
        if self.online:
            img_str = img_fp.dumps()
            try:
                return self.client("ocr_for_single_line", self.lang, img_str)
            except:
                self.online = False
        from module.ocr.models import OCR_MODEL
        return OCR_MODEL.__getattribute__(self.lang).ocr_for_single_line(img_fp)

    def ocr_for_single_lines(self, img_list: List[np.ndarray]):
        if self.online:
            img_str_list = [img_fp.dumps() for img_fp in img_list]
            try:
                return self.client("ocr_for_single_lines", self.lang, img_str_list)
            except:
                self.online = False
        from module.ocr.models import OCR_MODEL
        return OCR_MODEL.__getattribute__(self.lang).ocr_for_single_lines(img_list)

    def set_cand_alphabet(self, cand_alphabet: str):
        if self.online:
            try:
                return self.client("set_cand_alphabet", self.lang, cand_alphabet)
            except:
                self.online = False
        from module.ocr.models import OCR_MODEL
        return OCR_MODEL.__getattribute__(self.lang).set_cand_alphabet(cand_alphabet)

    def debug(self, img_list: List[np.ndarray]):
        if self.online:
            img_str_list = [img_fp.dumps() for img_fp in img_list]
            try:
                return self.client("debug", self.lang, img_str_list)
            except:
                self.online = False
        from module.ocr.models import OCR_MODEL
        return OCR_MODEL.__getattribute__(self.lang).debug(img_list)


class ModelProxyFactory:
    def __getattribute__(self, __name: str) -> ModelProxy:
        if __name in ["azur_lane", "cnocr", "jp", "tw"]:
            if ModelProxy.client is None:
                ModelProxy.init(address=State.deploy_config.OcrClientAddress)
            return ModelProxy(lang=__name)
        else:
            return super().__getattribute__(__name)


def start_ocr_server(port=22268):
    from module.ocr.al_ocr import AlOcr
    from module.ocr.models import OcrModel

    class OCRServer(OcrModel):
        def hello(self):
            return "hello"

        def ocr(self, lang, img_fp):
            img_fp = pickle.loads(img_fp)
            cnocr: AlOcr = self.__getattribute__(lang)
            return cnocr.ocr(img_fp)

        def ocr_for_single_line(self, lang, img_fp):
            img_fp = pickle.loads(img_fp)
            cnocr: AlOcr = self.__getattribute__(lang)
            return cnocr.ocr_for_single_line(img_fp)

        def ocr_for_single_lines(self, lang, img_list):
            img_list = [pickle.loads(img_fp) for img_fp in img_list]
            cnocr: AlOcr = self.__getattribute__(lang)
            return cnocr.ocr_for_single_lines(img_list)

        def set_cand_alphabet(self, lang, cand_alphabet):
            cnocr: AlOcr = self.__getattribute__(lang)
            return cnocr.set_cand_alphabet(cand_alphabet)

        def debug(self, lang, img_list):
            img_list = [pickle.loads(img_fp) for img_fp in img_list]
            cnocr: AlOcr = self.__getattribute__(lang)
            return cnocr.debug(img_list)

    server = zerorpc.Server(OCRServer())
    try:
        server.bind(f"tcp://*:{port}")
    except zmq.error.ZMQError:
        logger.error(f"Ocr server cannot bind on port {port}")
        return
    logger.info(f"Ocr server listen on port {port}")
    server.run()


def start_ocr_server_process(port=22268):
    global process
    if not alive():
        process = multiprocessing.Process(target=start_ocr_server, args=(port,))
        process.start()


def stop_ocr_server_process():
    global process
    if alive():
        process.kill()
        process = None


def alive() -> bool:
    global process
    if process is not None:
        return process.is_alive()
    else:
        return False


if __name__ == "__main__":
    # Run server
    parser = argparse.ArgumentParser(description="Alas OCR service")
    parser.add_argument(
        "--port",
        type=int,
        help="Port to listen. Default to OcrServerPort in deploy setting",
    )
    args, _ = parser.parse_known_args()
    port = args.port or State.deploy_config.OcrServerPort
    start_ocr_server(port=port)
