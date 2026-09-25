import http.client
import json
import socket
import struct
import threading
import time
from functools import wraps
from urllib.parse import quote, urlparse

import cv2
import numpy as np
from lxml import etree

from module.base.decorator import cached_property, del_cached_property, has_cached_property
from module.base.utils import ensure_time, image_size, random_rectangle_point
from module.device.method.utils import RETRY_TRIES, retry_sleep
from module.exception import GameNotRunningError, RequestHumanTakeover
from module.logger import logger


PLAYCOVER_DEFAULT_HOST = '127.0.0.1'
PLAYCOVER_DEFAULT_PORT = 1717
PLAYCOVER_MANAGER_DEFAULT_PORT = 1718
PLAYCOVER_SERIAL_SCHEMES = ('playcover', 'maatools')
PLAYCOVER_MANAGER_SERIAL_SCHEMES = ('playcoverm', 'pm')
PLAYCOVER_SHORT_SWIPE_DISTANCE = 80
PLAYCOVER_SHORT_SWIPE_SPEED = 5
PLAYCOVER_SHORT_SWIPE_MIN_STEPS = 8
PLAYCOVER_SHORT_SWIPE_INTERVAL = 0.025
PLAYCOVER_SWIPE_INTERVAL = 0.010
PLAYCOVER_TOUCH_SYNC_TIMEOUT = 5
# Shared delivery budget, failure cleanup, and network allowance: 3 + 3 + 2 seconds.
PLAYCOVER_TOUCH_SEQUENCE_TIMEOUT_MARGIN = 8
PLAYCOVER_TOUCH_SEQUENCE_MAX_EVENTS = 1024
PLAYCOVER_TOUCH_SEQUENCE_MAX_DELAY = 30
PLAYCOVER_TOUCH_SEQUENCE_MAX_DURATION_US = 120_000_000
PLAYCOVER_MAATOOLS_READY_TIMEOUT = 15
PLAYCOVER_MAATOOLS_READY_INTERVAL = 0.5


class MaaToolsManagerError(Exception):
    def __init__(self, message, status=None, result=None):
        super().__init__(message)
        self.status = status
        self.result = result


class MaaToolsBundleMismatch(MaaToolsManagerError):
    pass


class MaaToolsPortConflict(MaaToolsManagerError):
    pass


class MaaToolsClientError(Exception):
    pass


class MaaToolsTouchError(MaaToolsClientError):
    """A failed gesture must not be automatically replayed."""


class PlayCoverDataTruncated(MaaToolsClientError):
    pass


class PlayCoverDataTimeout(MaaToolsClientError):
    pass


def retry(func):
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (PlayCover):
        """
        init = None
        for trial in range(RETRY_TRIES):
            if callable(init):
                time.sleep(retry_sleep(trial))
                init()

            try:
                return func(self, *args, **kwargs)
            # Can't handle
            except RequestHumanTakeover:
                break
            # Let the scheduler run the normal restart and login workflow.
            except GameNotRunningError:
                raise
            # Restarting the target app cannot resolve a configured port conflict.
            except (MaaToolsBundleMismatch, MaaToolsPortConflict) as e:
                logger.critical(e)
                break
            except MaaToolsTouchError as e:
                logger.critical(e)
                self.maatools_client_release()
                raise RequestHumanTakeover from e
            # MaaTools manager
            except MaaToolsManagerError as e:
                logger.error(e)

                def init():
                    self.maatools_manager_release()
            # MaaTools connection lost or invalid response
            except MaaToolsClientError as e:
                logger.error(e)

                def init():
                    self.maatools_client_release()
            # Unknown
            except Exception as e:
                logger.exception(e)

                def init():
                    self.maatools_client_release()

        logger.critical(f'Retry {func.__name__}() failed')
        self.maatools_manager_release()
        raise RequestHumanTakeover

    return retry_wrapper


def _parse_playcover_address(serial: str, schemes, default_port):
    serial = str(serial or '').strip()
    lowered = serial.lower()
    if not serial or lowered == 'auto' or lowered in schemes:
        return PLAYCOVER_DEFAULT_HOST, default_port

    for scheme in schemes:
        prefix = f'{scheme}://'
        if lowered.startswith(prefix):
            parsed = urlparse(serial)
            host = parsed.hostname or PLAYCOVER_DEFAULT_HOST
            port = parsed.port or default_port
            return host, port

        prefix = f'{scheme}:'
        if lowered.startswith(prefix):
            value = serial[len(prefix):]
            if not value:
                return PLAYCOVER_DEFAULT_HOST, default_port
            host, sep, port = value.rpartition(':')
            if sep:
                return host or PLAYCOVER_DEFAULT_HOST, int(port)
            return value, default_port

    host, sep, port = serial.rpartition(':')
    if sep:
        return host or PLAYCOVER_DEFAULT_HOST, int(port)
    return serial or PLAYCOVER_DEFAULT_HOST, default_port


def is_playcover_manager_serial(serial: str):
    serial = str(serial or '').strip().lower()
    return serial in PLAYCOVER_MANAGER_SERIAL_SCHEMES or any(
        serial.startswith(f'{scheme}:') for scheme in PLAYCOVER_MANAGER_SERIAL_SCHEMES
    )


def is_playcover_serial(serial: str):
    serial = str(serial or '').strip().lower()
    schemes = PLAYCOVER_SERIAL_SCHEMES + PLAYCOVER_MANAGER_SERIAL_SCHEMES
    return serial in schemes or any(serial.startswith(f'{scheme}:') for scheme in schemes)


def parse_playcover_serial(serial: str):
    """
    Args:
        serial: playcover, playcover://host:port, playcover:host:port,
            maatools://host:port, maatools:host:port, or host:port.

    Returns:
        tuple[str, int]:
    """
    return _parse_playcover_address(serial, PLAYCOVER_SERIAL_SCHEMES, PLAYCOVER_DEFAULT_PORT)


def parse_playcover_manager_serial(serial: str):
    """
    Args:
        serial: playcoverm, playcoverm://host:port, playcoverm:host:port,
            pm://host:port, or pm:host:port.

    Returns:
        tuple[str, int]:
    """
    if not is_playcover_manager_serial(serial):
        raise ValueError(f'Not a PlayCover manager serial: {serial}')
    return _parse_playcover_address(
        serial,
        PLAYCOVER_MANAGER_SERIAL_SCHEMES,
        PLAYCOVER_MANAGER_DEFAULT_PORT,
    )


def insert_swipe(p0, p3, speed=15, min_steps=2):
    """
    Insert way point from start to end.
    """
    p0 = np.array(p0, dtype=float)
    p3 = np.array(p3, dtype=float)
    distance = np.linalg.norm(p3 - p0)
    steps = max(int(distance / speed) + 1, min_steps)
    points = []
    for index in range(steps):
        ratio = index / (steps - 1)
        point = p0 * (1 - ratio) + p3 * ratio
        points.append(point.astype(int).tolist())
    return points


def playcover_empty_hierarchy():
    return etree.Element('hierarchy')


class MaaToolsClient:
    connection_magic = b'MAA\x00'
    bgr_screencap_magic = b'BGR\x01'
    native_screencap_magic = b'NATV'
    size_magic = b'SIZE'
    touch_magic = b'TUCH'
    touch_sync_magic = b'TSYN'
    touch_sequence_magic = b'TSEQ'
    version_magic = b'VERN'
    bundle_magic = b'BNDL'

    def __init__(
            self,
            host=PLAYCOVER_DEFAULT_HOST,
            port=PLAYCOVER_DEFAULT_PORT,
            timeout=3,
            expected_bundle_identifier='',
    ):
        self.host = host
        self.port = int(port)
        self.timeout = timeout
        self.expected_bundle_identifier = str(expected_bundle_identifier or '').strip()
        self.sock = None
        self.lock = threading.Lock()
        self.max_x = 1280
        self.max_y = 720
        self.version = 0
        self.bundle_identifier = None
        self.screenshot_method = None

    def connect(self):
        self.disconnect()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            logger.attr('PlayCover', f'{self.host}:{self.port}')
            sock.connect((self.host, self.port))
            self.sock = sock
            self._handshake()
            self.version = self.get_version()
            self.bundle_identifier = self.get_bundle_identifier()
            if self.expected_bundle_identifier \
                    and self.bundle_identifier != self.expected_bundle_identifier:
                raise MaaToolsBundleMismatch(
                    f'PlayCover MaaTools bundle mismatch at {self.host}:{self.port}: '
                    f'{self.bundle_identifier!r}, expected {self.expected_bundle_identifier!r}. '
                    f'Configure a unique MaaTools port for each concurrently running app'
                )
            self.max_x, self.max_y = self.get_window_size()
            logger.attr('PlayCoverMaaToolsVersion', self.version)
            if self.bundle_identifier:
                logger.attr('PlayCoverBundle', self.bundle_identifier)
            logger.attr('PlayCoverWindow', f'{self.max_x}x{self.max_y}')
        except (MaaToolsManagerError, MaaToolsClientError):
            self.disconnect()
            raise
        except OSError as e:
            self.disconnect()
            raise MaaToolsClientError(
                f'Unable to connect PlayCover MaaTools at {self.host}:{self.port}: {e}'
            ) from e
        return self

    def disconnect(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def _send_message(self, magic, payload=b''):
        try:
            self.sock.sendall(struct.pack('>H', 4 + len(payload)) + magic + payload)
        except socket.timeout as e:
            raise PlayCoverDataTimeout(f'PlayCover MaaTools send timed out: {e}') from e
        except OSError as e:
            raise MaaToolsClientError(f'PlayCover MaaTools send failed: {e}') from e

    def _recv_exact(self, size, deadline=None):
        data = bytearray(size)
        view = memoryview(data)
        received = 0
        while received < size:
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise PlayCoverDataTimeout(f'PlayCover MaaTools response timed out at {received}/{size}')
                self.sock.settimeout(remaining)
            try:
                length = self.sock.recv_into(view[received:], size - received)
            except socket.timeout as e:
                raise PlayCoverDataTimeout(
                    f'PlayCover MaaTools receive timed out at {received}/{size}: {e}'
                ) from e
            except OSError as e:
                raise MaaToolsClientError(f'PlayCover MaaTools receive failed: {e}') from e
            if not length:
                raise PlayCoverDataTruncated(f'Incomplete data received: {received}/{size}')
            received += length
        return data

    def _handshake(self):
        self.sock.sendall(self.connection_magic)
        response = self._recv_exact(4)
        if response != b'OKAY':
            raise MaaToolsClientError(f'PlayCover MaaTools handshake failed: {response!r}')

    def get_window_size(self):
        with self.lock:
            self._send_message(self.size_magic)
            data = self._recv_exact(4)
        return struct.unpack('>HH', data)

    def get_version(self):
        with self.lock:
            self._send_message(self.version_magic)
            data = self._recv_exact(4)
        return struct.unpack('>I', data)[0]

    def get_bundle_identifier(self):
        with self.lock:
            self._send_message(self.bundle_magic)
            size = struct.unpack('>I', self._recv_exact(4))[0]
            if not 1 <= size <= 4096:
                raise PlayCoverDataTruncated(f'Invalid PlayCover MaaTools bundle length: {size}')
            data = self._recv_exact(size)
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError as e:
            raise PlayCoverDataTruncated('Invalid PlayCover MaaTools bundle identifier') from e

    def convert(self, x, y, source_size=None):
        if source_size is None:
            source_size = self.max_x, self.max_y
        source_width, source_height = source_size
        if source_width <= 0 or source_height <= 0:
            raise MaaToolsClientError(f'Invalid PlayCover touch source size: {source_size}')
        x = int(round(int(x) / source_width * self.max_x))
        y = int(round(int(y) / source_height * self.max_y))
        x = max(0, min(x, self.max_x - 1))
        y = max(0, min(y, self.max_y - 1))
        return x, y

    def send_touch(self, phase, x=0, y=0, source_size=None):
        x, y = self.convert(x, y, source_size=source_size)
        payload = struct.pack('>BHH', int(phase), x, y)
        with self.lock:
            self._send_message(self.touch_magic, payload)

    def sync_touch(self):
        if self.version < 5:
            return False

        with self.lock:
            timeout = self.sock.gettimeout()
            self.sock.settimeout(max(timeout or self.timeout, PLAYCOVER_TOUCH_SYNC_TIMEOUT))
            try:
                self._send_message(self.touch_sync_magic)
                response = self._recv_exact(4)
            finally:
                self.sock.settimeout(timeout)
        if response != b'OKAY':
            raise MaaToolsClientError(f'PlayCover MaaTools touch sync failed: {response!r}')
        return True

    def send_touch_sequence(self, events, source_size=None):
        """
        Args:
            events (list[tuple[float, int, int, int]]): Delay in seconds before each
                event, TUCH phase, x, y. Must contain complete down/move*/up gestures.
            source_size: Same screenshot coordinate space as send_touch().

        A failure may follow partial execution. Never retry or fall back after sending.
        """
        if self.version < 5:
            raise MaaToolsClientError('PlayCover touch sequences require MaaTools v5')
        if not 2 <= len(events) <= PLAYCOVER_TOUCH_SEQUENCE_MAX_EVENTS:
            raise MaaToolsClientError(f'Invalid PlayCover touch sequence length: {len(events)}')

        payload = bytearray(struct.pack('>H', len(events)))
        total_delay = 0
        active = False
        for delay, phase, x, y in events:
            if not 0 <= delay <= PLAYCOVER_TOUCH_SEQUENCE_MAX_DELAY:
                raise MaaToolsClientError(f'Invalid PlayCover touch sequence delay: {delay}')
            delay_us = int(round(delay * 1_000_000))
            total_delay += delay_us
            if total_delay > PLAYCOVER_TOUCH_SEQUENCE_MAX_DURATION_US:
                raise MaaToolsClientError('PlayCover touch sequence exceeds 120 seconds')
            if phase == 0 and not active:
                active = True
            elif phase in (1, 3) and active:
                active = phase != 3
            else:
                raise MaaToolsClientError(f'Invalid PlayCover touch sequence phase: {phase}')
            x, y = self.convert(x, y, source_size=source_size)
            payload.extend(struct.pack('>IBHH', delay_us, int(phase), x, y))
        if active:
            raise MaaToolsClientError('PlayCover touch sequence must end with touch up')

        with self.lock:
            sock = self.sock
            timeout = sock.gettimeout()
            budget = max(timeout or self.timeout or 0, total_delay / 1_000_000
                         + PLAYCOVER_TOUCH_SEQUENCE_TIMEOUT_MARGIN)
            deadline = time.monotonic() + budget
            try:
                try:
                    sock.settimeout(budget)
                    self._send_message(self.touch_sequence_magic, payload)
                    response = self._recv_exact(4, deadline=deadline)
                    if response != b'OKAY':
                        raise MaaToolsClientError(f'PlayCover touch sequence failed: {response!r}')
                finally:
                    sock.settimeout(timeout)
            except BaseException:
                # Discard late/partial responses and cancel this connection's active touch.
                self.disconnect()
                raise

    def _log_screenshot_method(self, method):
        if self.screenshot_method != method:
            logger.attr('PlayCoverScreenshot', method)
            self.screenshot_method = method

    def screenshot_bgr(self):
        with self.lock:
            self._send_message(self.bgr_screencap_magic)
            width, height, size = struct.unpack('>III', self._recv_exact(12))
            data = self._recv_exact(size)
        expected = width * height * 3
        if expected <= 0 or len(data) != expected:
            raise PlayCoverDataTruncated(
                f'Unexpected PlayCover BGR screenshot size: {len(data)}, '
                f'expected {expected} from {width}x{height}'
            )
        image = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))
        cv2.cvtColor(image, cv2.COLOR_BGR2RGB, dst=image)
        return image

    def screenshot_native(self):
        with self.lock:
            self._send_message(self.native_screencap_magic)
            width, height, image_format, size = struct.unpack('>II4sI', self._recv_exact(16))
            data = self._recv_exact(size)
        if image_format != b'BGR3':
            raise PlayCoverDataTruncated(f'Unexpected PlayCover native screenshot format: {image_format!r}')
        expected = width * height * 3
        if expected <= 0 or len(data) != expected:
            raise PlayCoverDataTruncated(
                f'Unexpected PlayCover native screenshot size: {len(data)}, '
                f'expected {expected} from {width}x{height}'
            )
        image = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))
        cv2.cvtColor(image, cv2.COLOR_BGR2RGB, dst=image)
        return image

    def screenshot(self):
        if self.version >= 5:
            self._log_screenshot_method('NATV')
            return self.screenshot_native()
        self._log_screenshot_method('BGR')
        return self.screenshot_bgr()


class PlayCoverManager:
    def __init__(
            self,
            host=PLAYCOVER_DEFAULT_HOST,
            port=PLAYCOVER_MANAGER_DEFAULT_PORT,
            key='',
            timeout=3,
    ):
        self.host = host
        self.port = int(port)
        self.key = str(key or '')
        self.timeout = timeout

    def _request(self, method, path, body=None, timeout=None):
        payload = b''
        headers = {
            'Accept': 'application/json',
        }
        if body is not None:
            payload = json.dumps(body).encode('utf-8')
            headers['Content-Type'] = 'application/json; charset=utf-8'
        if self.key:
            headers['X-PlayCover-Key'] = self.key

        conn = http.client.HTTPConnection(self.host, self.port, timeout=timeout or self.timeout)
        try:
            conn.request(method, path, body=payload, headers=headers)
            response = conn.getresponse()
            data = response.read()
        except (OSError, http.client.HTTPException) as e:
            raise MaaToolsManagerError(
                f'PlayCover manager is not reachable at {self.host}:{self.port}: {e}'
            ) from e
        finally:
            conn.close()

        try:
            result = json.loads(data.decode('utf-8')) if data else {}
        except ValueError:
            result = {'raw': data.decode('utf-8', errors='replace')}

        if response.status >= 400:
            raise MaaToolsManagerError(
                f'PlayCover manager {method} {path} failed: HTTP {response.status}, {result}',
                status=response.status,
                result=result,
            )
        return result

    @staticmethod
    def _app_path(bundle_identifier):
        return f'/apps/{quote(bundle_identifier, safe="")}'

    def app_status(self, bundle_identifier, timeout=3):
        return self._request('GET', self._app_path(bundle_identifier), timeout=timeout)

    def list_apps(self, timeout=3):
        result = self._request('GET', '/apps', timeout=timeout)
        apps = result.get('apps') if isinstance(result, dict) else None
        if not isinstance(apps, list):
            raise MaaToolsManagerError(f'Invalid PlayCover manager app list: {result}')
        return apps

    def app_stop(self, bundle_identifier, timeout=10, force=False):
        return self._request('POST', f'{self._app_path(bundle_identifier)}/stop', {
            'timeout': timeout,
            'force': force,
        }, timeout=timeout + 10)


class MaaToolsManager(PlayCoverManager):
    def __init__(
            self,
            bundle_identifier,
            host=PLAYCOVER_DEFAULT_HOST,
            port=PLAYCOVER_MANAGER_DEFAULT_PORT,
            key='',
            timeout=3,
    ):
        super().__init__(host=host, port=port, key=key, timeout=timeout)
        self.bundle_identifier = str(bundle_identifier or '').strip()
        if not self.bundle_identifier:
            raise ValueError('PlayCover bundle identifier is required for MaaTools manager')
        self.maatools_port = None

    def maatools_open(self, port=None, restart=True, timeout=15, port_timeout=15, fresh='off'):
        fresh = str(fresh or 'off')
        if fresh not in ('off', 'fallback', 'always'):
            raise ValueError(f'Invalid PlayCover fresh mode: {fresh!r}')
        if not restart and fresh != 'off':
            raise ValueError('PlayCover fresh mode requires restart=True')

        launch_attempts = 2 if fresh == 'fallback' else 1
        if restart:
            stop_budget = timeout + 5
            cleanup_budget = 10 if fresh == 'fallback' else 0
            request_timeout = (
                stop_budget
                + min(5, timeout)
                + launch_attempts * (timeout + port_timeout)
                + cleanup_budget
                + 15
            )
        else:
            request_timeout = timeout + 15
        body = {
            'restart': restart,
            'timeout': timeout,
            'portTimeout': port_timeout,
            'fresh': fresh,
        }
        if port is not None:
            body['port'] = int(port)
        return self._request(
            'POST', f'{self._app_path(self.bundle_identifier)}/maatools/open',
            body, timeout=request_timeout,
        )

    def _checked_status(self):
        status = self.app_status(self.bundle_identifier)
        self._validate_maatools_bundle(status)
        self._validate_status(status)
        return status

    def launch(self):
        status = self._checked_status()
        maatools = status['maaTools']
        if status['running'] and maatools['enabled']:
            try:
                return self._wait_until_ready(status)
            except GameNotRunningError as e:
                logger.warning(f'{e}, restarting app')

        return self.restart()

    def attach(self):
        return self._wait_until_ready(self._checked_status())

    def _wait_until_ready(self, status, timeout=PLAYCOVER_MAATOOLS_READY_TIMEOUT):
        if not status['running']:
            raise GameNotRunningError('PlayCover app is not running')
        if not status['maaTools']['enabled']:
            raise GameNotRunningError('PlayCover MaaTools is not enabled')

        timeout = max(0, float(timeout))
        deadline = time.monotonic() + timeout
        waiting_logged = False
        while not self.status_ready(status):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise GameNotRunningError('PlayCover MaaTools is not ready')
            if not waiting_logged:
                logger.info(f'Wait up to {timeout:g}s for PlayCover MaaTools')
                waiting_logged = True
            time.sleep(min(PLAYCOVER_MAATOOLS_READY_INTERVAL, remaining))
            status = self._checked_status()
            if not status['running']:
                raise GameNotRunningError('PlayCover app stopped before MaaTools was ready')
            if not status['maaTools']['enabled']:
                raise GameNotRunningError('PlayCover MaaTools was disabled while waiting')

        self._set_maatools_port(status)
        logger.info('Reuse running PlayCover app')
        return self

    def restart(self):
        try:
            status = self.maatools_open(restart=True, fresh='fallback')
        except MaaToolsManagerError as e:
            result = e.result if isinstance(e.result, dict) else {}
            self._validate_maatools_bundle(result)
            if result.get('error') == 'maatools_port_in_use':
                raise MaaToolsPortConflict(
                    f'PlayCover MaaTools port conflict at {self.host}: '
                    f'the configured port is occupied by an unidentified service'
                ) from e
            status = result.get('status')
            self._log_launch_result(status)
            self._validate_maatools_bundle(status)
            raise
        self._log_launch_result(status)
        self._validate_maatools_bundle(status)
        self._validate_status(status)
        self._set_maatools_port(status)
        return self

    @staticmethod
    def status_ready(status):
        maatools = status.get('maaTools') if isinstance(status, dict) else None
        return bool(
            isinstance(maatools, dict)
            and status.get('running')
            and maatools.get('enabled')
            and maatools.get('reachable')
        )

    def _validate_status(self, status):
        maatools = status.get('maaTools') if isinstance(status, dict) else None
        valid = (
            isinstance(status, dict)
            and str(status.get('bundleIdentifier') or '').strip() == self.bundle_identifier
            and isinstance(status.get('running'), bool)
            and isinstance(maatools, dict)
            and isinstance(maatools.get('enabled'), bool)
            and isinstance(maatools.get('reachable'), bool)
            and isinstance(maatools.get('port'), int)
            and not isinstance(maatools.get('port'), bool)
            and 1024 <= maatools.get('port') <= 65535
        )
        if not valid:
            raise MaaToolsManagerError(f'Invalid PlayCover manager app status: {status}')

    def _validate_maatools_bundle(self, status):
        if not isinstance(status, dict):
            return

        maatools = status.get('maaTools')
        if isinstance(maatools, dict):
            bundle_identifier = str(maatools.get('bundleIdentifier') or '').strip()
            port = maatools.get('port') or self.maatools_port or 'unknown'
        elif status.get('error') == 'maatools_port_in_use':
            bundle_identifier = str(status.get('bundleIdentifier') or '').strip()
            port = self.maatools_port or 'unknown'
        else:
            return

        if not bundle_identifier or not self.bundle_identifier \
                or bundle_identifier == self.bundle_identifier:
            return
        raise MaaToolsBundleMismatch(
            f'PlayCover MaaTools bundle mismatch at {self.host}:{port}: '
            f'{bundle_identifier!r}, expected {self.bundle_identifier!r}. '
            f'Configure a unique MaaTools port for each concurrently running app'
        )

    def _set_maatools_port(self, status):
        maatools = status.get('maaTools') if isinstance(status, dict) else None
        try:
            port = int(maatools.get('port') or 0)
        except (AttributeError, TypeError, ValueError):
            port = 0
        if not 1024 <= port <= 65535:
            raise MaaToolsManagerError(f'Invalid MaaTools port in PlayCover manager response: {status}')
        self.maatools_port = port

    @staticmethod
    def _log_launch_result(status):
        if not isinstance(status, dict):
            return
        launch = status.get('launch') or {}
        if not isinstance(launch, dict) or not launch.get('fallbackUsed'):
            return

        attempts = launch.get('attempts') or []
        first = attempts[0] if attempts and isinstance(attempts[0], dict) else {}
        final = attempts[-1] if attempts and isinstance(attempts[-1], dict) else {}
        first_outcome = first.get('outcome') or 'unknown'
        elapsed = first.get('elapsedMs')
        detail = f'first attempt: {first_outcome}'
        if isinstance(elapsed, int):
            detail += f' after {elapsed / 1000:.2f}s'

        if final.get('outcome') == 'ready':
            logger.warning(f'PlayCover recovered MaaTools with a fresh launch ({detail})')
        else:
            final_outcome = final.get('outcome') or 'unknown'
            logger.warning(
                f'PlayCover used a fresh launch fallback but recovery failed '
                f'({detail}, final attempt: {final_outcome})'
            )


class PlayCover:
    _playcover_hierarchy_warned = False

    def _playcover_manager_endpoint(self):
        host, port = parse_playcover_manager_serial(self.serial)
        logger.attr('PlayCoverManager', f'{host}:{port}')
        return host, port, getattr(self.config, 'PlayCover_ManagerKey', '')

    def _new_playcover_manager(self):
        host, port, key = self._playcover_manager_endpoint()
        return PlayCoverManager(host=host, port=port, key=key)

    def _new_maatools_manager(self, bundle_identifier):
        host, port, key = self._playcover_manager_endpoint()
        return MaaToolsManager(
            bundle_identifier=bundle_identifier,
            host=host,
            port=port,
            key=key,
        )

    def list_package_playcover(self, show_log=True):
        if show_log:
            logger.info('Get package list')
        if not self.playcover_manager_configured():
            from module.config.server import to_package
            logger.warning('PackageName auto cannot be detected without PlayCover manager, defaulting to CN')
            return [to_package('cn')]

        try:
            apps = self._new_playcover_manager().list_apps()
        except MaaToolsManagerError as e:
            logger.critical(e)
            logger.critical('PlayCover manager API is required by the selected Serial')
            raise RequestHumanTakeover

        return [
            str(app.get('bundleIdentifier') or '').strip()
            for app in apps
            if isinstance(app, dict) and str(app.get('bundleIdentifier') or '').strip()
        ]

    @cached_property
    def maatools_manager(self):
        return self._new_maatools_manager(bundle_identifier=self.package)

    @cached_property
    def maatools_client(self):
        manager = None
        if self.playcover_manager_configured():
            manager = self.maatools_manager
            if manager.maatools_port is None:
                manager.attach()
            host, port = manager.host, manager.maatools_port
        else:
            host, port = parse_playcover_serial(self.serial)

        client = MaaToolsClient(
            host=host,
            port=port,
            expected_bundle_identifier=self.package,
        )
        try:
            return client.connect()
        except MaaToolsBundleMismatch:
            if manager is None:
                raise

            status = manager._checked_status()
            was_ready = manager.status_ready(status)
            previous_port = manager.maatools_port
            manager._wait_until_ready(status)
            if was_ready and manager.maatools_port == previous_port:
                raise
            if manager.maatools_port != previous_port:
                logger.info(
                    f'PlayCover MaaTools port changed '
                    f'{previous_port} -> {manager.maatools_port}'
                )
        except MaaToolsClientError:
            if manager is None:
                raise

            status = manager._checked_status()
            was_ready = manager.status_ready(status)
            previous_port = manager.maatools_port
            manager._wait_until_ready(status)
            if was_ready and manager.maatools_port == previous_port:
                raise
            if manager.maatools_port != previous_port:
                logger.info(
                    f'PlayCover MaaTools port changed '
                    f'{previous_port} -> {manager.maatools_port}'
                )

        client = MaaToolsClient(
            host=manager.host,
            port=manager.maatools_port,
            expected_bundle_identifier=self.package,
        )
        return client.connect()

    def maatools_client_release(self, show_log=True):
        if has_cached_property(self, 'maatools_client'):
            self.maatools_client.disconnect()
            del_cached_property(self, 'maatools_client')
            if show_log:
                logger.info('PlayCover MaaTools client released')

    def maatools_manager_release(self):
        manager_cached = has_cached_property(self, 'maatools_manager')
        self.maatools_client_release(show_log=not manager_cached)
        if manager_cached:
            del_cached_property(self, 'maatools_manager')
            logger.info('PlayCover MaaTools manager released')

    def playcover_manager_configured(self):
        return is_playcover_manager_serial(self.serial)

    def app_current_playcover(self):
        return self.package

    @retry
    def app_start_playcover(self):
        if not self.playcover_manager_configured():
            logger.info('App start is skipped for PlayCover; manager API is disabled')
            return

        self.maatools_manager.launch()
        _ = self.maatools_client

    @retry
    def app_stop_playcover(self):
        if not self.playcover_manager_configured():
            logger.info('App stop is skipped for PlayCover; manager API is disabled')
            return

        manager = self.__dict__.get('maatools_manager')
        if manager is None:
            manager = self._new_playcover_manager()
        manager.app_stop(self.package, timeout=10, force=False)
        self.maatools_manager_release()

    def app_is_running_playcover(self):
        if self.playcover_manager_configured():
            manager = self.__dict__.get('maatools_manager')
            if manager is None:
                manager = self._new_playcover_manager()
            try:
                status = manager.app_status(self.package)
                return isinstance(status, dict) and bool(status.get('running'))
            except MaaToolsManagerError as e:
                logger.warning(e)
                return False

        try:
            if has_cached_property(self, 'maatools_client'):
                self.maatools_client.get_window_size()
            else:
                host, port = parse_playcover_serial(self.serial)
                client = MaaToolsClient(
                    host=host,
                    port=port,
                    timeout=1,
                    expected_bundle_identifier=self.package,
                ).connect()
                client.disconnect()
            return True
        except (MaaToolsManagerError, MaaToolsClientError) as e:
            logger.warning(f'PlayCover MaaTools is not reachable: {e}')
            self.maatools_client_release()
            return False

    def dump_hierarchy_playcover(self):
        if not self._playcover_hierarchy_warned:
            logger.warning('Android UI hierarchy is not available on PlayCover, using an empty hierarchy')
            self._playcover_hierarchy_warned = True
        return playcover_empty_hierarchy()

    def get_orientation_playcover(self):
        return 0

    @retry
    def screenshot_playcover(self):
        return self.maatools_client.screenshot()

    def _maatools_touch_context(self):
        client = self.maatools_client
        image = getattr(self, 'image', None)
        source_size = image_size(image) if image is not None else (client.max_x, client.max_y)
        return client, source_size

    def _playcover_touch_sequence(self, events, post_delay=0.050):
        client, source_size = self._maatools_touch_context()
        try:
            if client.version >= 5:
                client.send_touch_sequence(events, source_size=source_size)
            else:
                for delay, phase, x, y in events:
                    if delay:
                        self.sleep(delay)
                    client.send_touch(phase, x, y, source_size=source_size)
            self.sleep(post_delay)
        except BaseException as e:
            client.disconnect()
            if isinstance(e, Exception):
                raise MaaToolsTouchError(f'PlayCover gesture failed; not replaying it: {e}') from e
            raise

    @retry
    def click_playcover(self, x, y):
        down = ensure_time((0.010, 0.020))
        self._playcover_touch_sequence(
            [(0, 0, x, y), (down, 3, x, y)], post_delay=0.050 - down)

    @retry
    def long_click_playcover(self, x, y, duration=1.0):
        self._playcover_touch_sequence([(0, 0, x, y), (ensure_time(duration), 3, x, y)])

    @retry
    def swipe_playcover(self, p1, p2):
        distance = np.linalg.norm(np.subtract(p1, p2))
        if distance < PLAYCOVER_SHORT_SWIPE_DISTANCE:
            points = insert_swipe(
                p0=p1,
                p3=p2,
                speed=PLAYCOVER_SHORT_SWIPE_SPEED,
                min_steps=PLAYCOVER_SHORT_SWIPE_MIN_STEPS,
            )
            interval = PLAYCOVER_SHORT_SWIPE_INTERVAL
        else:
            points = insert_swipe(p0=p1, p3=p2)
            interval = PLAYCOVER_SWIPE_INTERVAL
        if not points:
            return

        first = points[0]
        events = [(0, 0, first[0], first[1])]
        events.extend((interval, 1, point[0], point[1]) for point in points[1:])
        last = points[-1]
        events.append((interval, 3, last[0], last[1]))
        self._playcover_touch_sequence(events)

    @retry
    def drag_playcover(self, p1, p2, point_random=(-10, -10, 10, 10), hold_duration=0.0):
        p1 = np.array(p1) - random_rectangle_point(point_random)
        p2 = np.array(p2) - random_rectangle_point(point_random)
        points = insert_swipe(p0=p1, p3=p2, speed=20)
        if not points:
            return

        first = points[0]
        events = [(0, 0, first[0], first[1])]
        events.extend((0.010, 1, point[0], point[1]) for point in points[1:])
        events.append((0.010, 1, p2[0], p2[1]))
        events.append((0.140, 1, p2[0], p2[1]))

        hold_duration = ensure_time(hold_duration) - 0.28
        delay = 0.140
        if hold_duration > 0:
            events.append((delay, 1, p2[0], p2[1]))
            delay = hold_duration

        events.append((delay, 3, p2[0], p2[1]))
        self._playcover_touch_sequence(events)
