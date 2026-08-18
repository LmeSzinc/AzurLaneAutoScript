import argparse
import multiprocessing
import pickle
import socket
import struct
import threading
import time
from queue import Empty, Queue

from module.logger import logger
from module.webui.setting import State

process: multiprocessing.Process = None

# 4-byte big-endian length prefix + pickle payload
HEADER = struct.Struct(">I")

# Model methods that take a list of images and can be merged across
# concurrent connections into a single batched inference.
_BATCHABLE = {"ocr_for_single_lines", "atomic_ocr_for_single_lines"}

# How long the batch worker keeps collecting requests while under load (s).
# A lone request is dispatched immediately; the window only applies when
# several requests are already queued.
_BATCH_WINDOW = 0.02

# Watchdog: poll interval, initial backoff, backoff cap, and how long the
# server must stay alive before the backoff resets (s).
_WATCHDOG_POLL = 2.0
_WATCHDOG_BACKOFF_MIN = 2.0
_WATCHDOG_BACKOFF_MAX = 60.0
_WATCHDOG_STABLE_RESET = 60.0

_process_lock = threading.Lock()
_watchdog: threading.Thread | None = None


def _recv_all(sock: socket.socket, length: int) -> bytes:
    buf = bytearray()
    while len(buf) < length:
        chunk = sock.recv(length - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed by peer")
        buf.extend(chunk)
    return bytes(buf)


def _send_payload(sock: socket.socket, payload: bytes):
    sock.sendall(HEADER.pack(len(payload)) + payload)


class OcrRpcClient:
    """Synchronous RPC client for the OCR server, over plain TCP socket."""

    def __init__(self, address="127.0.0.1:22268", timeout=5):
        self.timeout = timeout
        host, _, port = address.rpartition(":")
        self.host = host or "127.0.0.1"
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
        if status == "ok":
            return result
        raise OcrServerError(result)


class OcrServerError(Exception):
    pass


class ModelProxy:
    client: OcrRpcClient = None
    online = True
    _last_reconnect = 0.0
    _reconnect_cooldown = 5.0

    @classmethod
    def init(cls, address="127.0.0.1:22268"):
        logger.info(f"Connecting to OCR server {address}")
        cls.client = OcrRpcClient(address=address)
        try:
            cls.client.connect()
            cls.client.call("hello")
            cls.online = True
            logger.info("Successfully connected to OCR server")
        except Exception:
            cls.online = False
            logger.warning("Ocr server not running")

    @classmethod
    def close(cls):
        if cls.client is not None:
            logger.info("Disconnect to OCR server")
            cls.client.close()
            logger.info("Successfully disconnected to OCR server")
            cls.client = None

    @classmethod
    def _reconnect(cls):
        """Reconnect after a server crash, throttled by a cooldown."""
        now = time.monotonic()
        if now - cls._last_reconnect < cls._reconnect_cooldown:
            return
        cls._last_reconnect = now
        if cls.client is None:
            cls.init()
            return
        try:
            cls.client.connect()
            cls.client.call("hello")
            cls.online = True
            logger.info("Reconnected to OCR server")
        except Exception:
            cls.client.close()

    def __init__(self, lang) -> None:
        self.lang = lang

    def _call(self, method, *args):
        if not self.online:
            self._reconnect()
        if self.online:
            try:
                return self.client.call(method, self.lang, *args)
            except Exception:
                self.online = False
        from module.ocr.models import OCR_MODEL

        return getattr(OCR_MODEL.__getattribute__(self.lang), method)(*args)

    def ocr(self, img_fp):
        return self._call("ocr", img_fp)

    def ocr_for_single_line(self, img_fp):
        return self._call("ocr_for_single_line", img_fp)

    def ocr_for_single_lines(self, img_list):
        return self._call("ocr_for_single_lines", img_list)

    def set_cand_alphabet(self, cand_alphabet: str):
        return self._call("set_cand_alphabet", cand_alphabet)

    def atomic_ocr(self, img_fp, cand_alphabet=None):
        return self._call("atomic_ocr", img_fp, cand_alphabet)

    def atomic_ocr_for_single_line(self, img_fp, cand_alphabet=None):
        return self._call("atomic_ocr_for_single_line", img_fp, cand_alphabet)

    def atomic_ocr_for_single_lines(self, img_list, cand_alphabet=None):
        return self._call("atomic_ocr_for_single_lines", img_list, cand_alphabet)

    def debug(self, img_list):
        return self._call("debug", img_list)


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
    """Single-process OCR server with cross-connection dynamic batching.

    Model sessions are singletons per language (OcrModel cached_property);
    a single batch worker drains all pending requests and merges same-model
    list calls into one inference run. A per-model lock guards cand_alphabet
    state so concurrent callers can no longer race on it.
    """

    def __init__(self):
        from module.ocr.models import OcrModel

        self._models = OcrModel()
        self._model_locks: dict[str, threading.Lock] = {}
        self._request_queue: Queue = Queue()
        self._worker = threading.Thread(target=self._batch_worker, daemon=True, name="ocr-batch-worker")
        self._worker.start()

    def _model(self, lang):
        return self._models.__getattribute__(lang)

    def _model_lock(self, lang) -> threading.Lock:
        return self._model_locks.setdefault(lang, threading.Lock())

    def hello(self):
        return "hello"

    def submit(self, conn: socket.socket, method: str, args: tuple):
        self._request_queue.put((conn, method, args))

    def _respond(self, conn: socket.socket, status: str, result):
        try:
            _send_payload(conn, pickle.dumps((status, result), protocol=pickle.HIGHEST_PROTOCOL))
        except OSError:
            pass

    def _batch_worker(self):
        while True:
            first = self._request_queue.get()
            pending = [first]
            # Drain everything already queued.
            while True:
                try:
                    pending.append(self._request_queue.get_nowait())
                except Empty:
                    break
            if len(pending) > 1:
                # Under load, wait a short window to collect a fuller batch.
                deadline = time.monotonic() + _BATCH_WINDOW
                while True:
                    try:
                        pending.append(self._request_queue.get(timeout=max(deadline - time.monotonic(), 0)))
                    except Empty:
                        break
            self._process_pending(pending)

    def _process_pending(self, pending: list[tuple[socket.socket, str, tuple]]):
        groups: dict[tuple[str, str, object], list[tuple[int, list]]] = {}
        singles: list[tuple[int, tuple]] = []
        for i, (conn, method, args) in enumerate(pending):
            if method in _BATCHABLE and len(args) >= 2 and isinstance(args[1], list):
                cand = args[2] if len(args) > 2 else None
                groups.setdefault((method, args[0], cand), []).append((i, args[1]))
            else:
                singles.append((i, (conn, method, args)))

        results: dict[int, object] = {}
        errors: dict[int, str] = {}
        for (method, lang, cand), items in groups.items():
            try:
                model = self._model(lang)
                with self._model_lock(lang):
                    if len(items) == 1:
                        i, img_list = items[0]
                        if method == "atomic_ocr_for_single_lines":
                            results[i] = model.atomic_ocr_for_single_lines(img_list, cand)
                        else:
                            results[i] = model.ocr_for_single_lines(img_list)
                    else:
                        merged = [img for _i, img_list in items for img in img_list]
                        if method == "atomic_ocr_for_single_lines":
                            out = model.atomic_ocr_for_single_lines(merged, cand)
                        else:
                            out = model.ocr_for_single_lines(merged)
                        pos = 0
                        for i, img_list in items:
                            n = len(img_list)
                            results[i] = out[pos : pos + n]
                            pos += n
            except Exception as e:
                logger.exception(e)
                for i, _img_list in items:
                    errors[i] = str(e)

        for i, (_conn, method, args) in singles:
            try:
                if method == "hello":
                    results[i] = self.hello()
                else:
                    lang = args[0]
                    model = self._model(lang)
                    with self._model_lock(lang):
                        results[i] = getattr(model, method)(*args[1:])
            except Exception as e:
                logger.exception(e)
                errors[i] = str(e)

        # Responses go out in arrival order so pipelined requests on the
        # same connection keep their order.
        for i, (conn, _method, _args) in enumerate(pending):
            if i in errors:
                self._respond(conn, "error", errors[i])
            else:
                self._respond(conn, "ok", results[i])


def _handle_connection(server: OCRServer, conn: socket.socket):
    try:
        while True:
            header = _recv_all(conn, HEADER.size)
            if len(header) < HEADER.size:
                break
            (length,) = HEADER.unpack(header)
            payload = _recv_all(conn, length)
            method, args = pickle.loads(payload)
            server.submit(conn, method, args)
    except (ConnectionError, OSError):
        pass
    finally:
        try:
            conn.close()
        except OSError:
            pass


def start_ocr_server(port=22268):
    # The OCR server is CPU-heavy; keep it below normal priority so inference
    # never starves the desktop while the bot runs 24/7.
    try:
        import psutil

        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass

    server = OCRServer()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listen_sock:
        listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            listen_sock.bind(("0.0.0.0", port))
        except OSError:
            logger.error(f"Ocr server cannot bind on port {port}")
            return
        listen_sock.listen()
        logger.info(f"Ocr server listen on port {port}")
        while True:
            conn, _ = listen_sock.accept()
            t = threading.Thread(target=_handle_connection, args=(server, conn), daemon=True)
            t.start()


def start_ocr_server_process(port=22268):
    global process, _watchdog
    with _process_lock:
        if not alive():
            process = multiprocessing.Process(target=start_ocr_server, args=(port,))
            process.start()
        if _watchdog is None or not _watchdog.is_alive():
            _watchdog = threading.Thread(target=_watchdog_loop, args=(port,), daemon=True, name="ocr-server-watchdog")
            _watchdog.start()


def stop_ocr_server_process():
    global process
    with _process_lock:
        if alive():
            process.kill()
        process = None


def alive() -> bool:
    global process
    if process is not None:
        return process.is_alive()
    else:
        return False


def _watchdog_loop(port):
    """Restart the OCR server if it crashes unexpectedly.

    Backoff grows exponentially up to _WATCHDOG_BACKOFF_MAX and resets once
    the server stays alive for _WATCHDOG_STABLE_RESET seconds. Deliberate
    stops (stop_ocr_server_process sets process to None) are not restarted.
    """
    global process
    delay = _WATCHDOG_BACKOFF_MIN
    stable_since = time.monotonic()
    while True:
        time.sleep(_WATCHDOG_POLL)
        with _process_lock:
            proc = process
            if proc is None:
                stable_since = time.monotonic()
                continue
            if proc.is_alive():
                if time.monotonic() - stable_since > _WATCHDOG_STABLE_RESET:
                    delay = _WATCHDOG_BACKOFF_MIN
                continue
        logger.warning(f"Ocr server died unexpectedly, restarting in {delay:.0f}s")
        time.sleep(delay)
        with _process_lock:
            if process is None:
                stable_since = time.monotonic()
                continue
            stable_since = time.monotonic()
            new = multiprocessing.Process(target=start_ocr_server, args=(port,))
            new.start()
            process = new
        delay = min(delay * 2, _WATCHDOG_BACKOFF_MAX)


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
