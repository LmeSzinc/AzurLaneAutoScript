import argparse
import multiprocessing
import pickle
import socket
import struct

from module.logger import logger
from module.webui.setting import State

process: multiprocessing.Process = None

# 4-byte big-endian length prefix + pickle payload
HEADER = struct.Struct('>I')


def _recv_all(sock: socket.socket, length: int) -> bytes:
    buf = bytearray()
    while len(buf) < length:
        chunk = sock.recv(length - len(buf))
        if not chunk:
            raise ConnectionError('Connection closed by peer')
        buf.extend(chunk)
    return bytes(buf)


def _send_payload(sock: socket.socket, payload: bytes):
    sock.sendall(HEADER.pack(len(payload)) + payload)


class OcrRpcClient:
    """Synchronous RPC client for the OCR server, over plain TCP socket."""

    def __init__(self, address='127.0.0.1:22268', timeout=5):
        self.timeout = timeout
        host, _, port = address.rpartition(':')
        self.host = host or '127.0.0.1'
        self.port = int(port)
        self.sock = None

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)

    def close(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def call(self, method, *args):
        _send_payload(self.sock, pickle.dumps((method, args), protocol=pickle.HIGHEST_PROTOCOL))
        header = _recv_all(self.sock, HEADER.size)
        (length,) = HEADER.unpack(header)
        payload = _recv_all(self.sock, length)
        status, result = pickle.loads(payload)
        if status == 'ok':
            return result
        raise OcrServerError(result)


class OcrServerError(Exception):
    pass


class ModelProxy:
    client: OcrRpcClient = None
    online = True

    @classmethod
    def init(cls, address="127.0.0.1:22268"):
        logger.info(f"Connecting to OCR server {address}")
        cls.client = OcrRpcClient(address=address)
        try:
            cls.client.connect()
            cls.client.call('hello')
            logger.info("Successfully connected to OCR server")
        except Exception:
            cls.online = False
            logger.warning("Ocr server not running")

    @classmethod
    def close(cls):
        if cls.client is not None:
            logger.info('Disconnect to OCR server')
            cls.client.close()
            logger.info('Successfully disconnected to OCR server')
            cls.client = None

    def __init__(self, lang) -> None:
        self.lang = lang

    def _call(self, method, *args):
        if self.online:
            try:
                return self.client.call(method, self.lang, *args)
            except Exception:
                self.online = False
        from module.ocr.models import OCR_MODEL
        return getattr(OCR_MODEL.__getattribute__(self.lang), method)(*args)

    def ocr(self, img_fp):
        return self._call('ocr', img_fp)

    def ocr_for_single_line(self, img_fp):
        return self._call('ocr_for_single_line', img_fp)

    def ocr_for_single_lines(self, img_list):
        return self._call('ocr_for_single_lines', img_list)

    def set_cand_alphabet(self, cand_alphabet: str):
        return self._call('set_cand_alphabet', cand_alphabet)

    def atomic_ocr(self, img_fp, cand_alphabet=None):
        return self._call('atomic_ocr', img_fp, cand_alphabet)

    def atomic_ocr_for_single_line(self, img_fp, cand_alphabet=None):
        return self._call('atomic_ocr_for_single_line', img_fp, cand_alphabet)

    def atomic_ocr_for_single_lines(self, img_list, cand_alphabet=None):
        return self._call('atomic_ocr_for_single_lines', img_list, cand_alphabet)

    def debug(self, img_list):
        return self._call('debug', img_list)


class ModelProxyFactory:
    def __getattribute__(self, __name: str) -> ModelProxy:
        if __name in ["azur_lane", "cnocr", "jp", "tw", "azur_lane_jp"]:
            if ModelProxy.client is None:
                ModelProxy.init(address=State.deploy_config.OcrClientAddress)
            return ModelProxy(lang=__name)
        else:
            return super().__getattribute__(__name)

    def close(self):
        ModelProxy.close()


class OCRServer:
    def __init__(self):
        from module.ocr.models import OcrModel
        self._models = OcrModel()

    def _model(self, lang):
        from module.ocr.al_ocr import AlOcr
        cnocr: AlOcr = self._models.__getattribute__(lang)
        return cnocr

    def hello(self):
        return "hello"

    def ocr(self, lang, img_fp):
        return self._model(lang).ocr(img_fp)

    def ocr_for_single_line(self, lang, img_fp):
        return self._model(lang).ocr_for_single_line(img_fp)

    def ocr_for_single_lines(self, lang, img_list):
        return self._model(lang).ocr_for_single_lines(img_list)

    def set_cand_alphabet(self, lang, cand_alphabet):
        return self._model(lang).set_cand_alphabet(cand_alphabet)

    def atomic_ocr(self, lang, img_fp, cand_alphabet):
        return self._model(lang).atomic_ocr(img_fp, cand_alphabet)

    def atomic_ocr_for_single_line(self, lang, img_fp, cand_alphabet):
        return self._model(lang).atomic_ocr_for_single_line(img_fp, cand_alphabet)

    def atomic_ocr_for_single_lines(self, lang, img_list, cand_alphabet):
        return self._model(lang).atomic_ocr_for_single_lines(img_list, cand_alphabet)

    def debug(self, lang, img_list):
        return self._model(lang).debug(img_list)


def _handle_connection(server: OCRServer, conn: socket.socket):
    try:
        while True:
            header = _recv_all(conn, HEADER.size)
            if len(header) < HEADER.size:
                break
            (length,) = HEADER.unpack(header)
            payload = _recv_all(conn, length)
            method, args = pickle.loads(payload)
            try:
                result = getattr(server, method)(*args)
                _send_payload(conn, pickle.dumps(('ok', result), protocol=pickle.HIGHEST_PROTOCOL))
            except Exception as e:
                logger.exception(e)
                _send_payload(conn, pickle.dumps(('error', str(e)), protocol=pickle.HIGHEST_PROTOCOL))
    except (ConnectionError, OSError):
        pass
    finally:
        try:
            conn.close()
        except OSError:
            pass


def start_ocr_server(port=22268):
    server = OCRServer()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listen_sock:
        listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            listen_sock.bind(('0.0.0.0', port))
        except OSError:
            logger.error(f"Ocr server cannot bind on port {port}")
            return
        listen_sock.listen()
        logger.info(f"Ocr server listen on port {port}")
        while True:
            conn, _ = listen_sock.accept()
            import threading
            t = threading.Thread(target=_handle_connection, args=(server, conn), daemon=True)
            t.start()


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
