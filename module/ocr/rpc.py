import argparse
import multiprocessing
import pickle
from typing import List

import numpy as np
import zerorpc
from deploy.config import DeployConfig
from module.logger import logger
from zerorpc.exceptions import LostRemote


class Config(DeployConfig):
    def show_config(self):
        pass

deploy_config = Config()
OCR_MODEL = None
process: multiprocessing.Process = None


class ModelProxy:
    client: zerorpc.Client = None

    @classmethod
    def init(cls, address="127.0.0.1:22268"):
        cls.client = zerorpc.Client()
        logger.info(f"Connecting to OCR server {address}")
        cls.client.connect(f"tcp://{address}")
        assert cls.client.hello() == "hello"
        logger.info("Successfully connected to OCR server")

    def __init__(self, lang) -> None:
        self.lang = lang

    def ocr(self, img_fp: np.ndarray):
        img_str = img_fp.dumps()
        return self.client("ocr", self.lang, img_str)

    def ocr_for_single_line(self, img_fp: np.ndarray):
        img_str = img_fp.dumps()
        return self.client("ocr_for_single_line", self.lang, img_str)

    def ocr_for_single_lines(self, img_list: List[np.ndarray]):
        img_str_list = [img_fp.dumps() for img_fp in img_list]
        return self.client("ocr_for_single_lines", self.lang, img_str_list)

    def set_cand_alphabet(self, cand_alphabet: str):
        return self.client("set_cand_alphabet", self.lang, cand_alphabet)


class ModelProxyFactory:
    def __getattribute__(self, __name: str) -> ModelProxy:
        global OCR_MODEL

        if ModelProxy.client is None:
            try:
                ModelProxy.init(address=deploy_config.config["OcrClientAddress"])
            except LostRemote:
                logger.warning("Ocr server not running")
                from module.ocr.models import OCR_MODEL
            except Exception as e:
                logger.exception(e)
                from module.ocr.models import OCR_MODEL

        if __name in ["azur_lane", "cnocr", "jp", "tw"]:
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

    server = zerorpc.Server(OCRServer())
    server.bind(f"tcp://*:{port}")
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
    port = args.port or deploy_config.config["OcrServerPort"]
    start_ocr_server(port=port)
