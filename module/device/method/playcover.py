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

from module.base.decorator import cached_property, del_cached_property, has_cached_property, set_cached_property
from module.base.utils import ensure_time, random_rectangle_point
from module.device.method.utils import RETRY_TRIES, retry_sleep
from module.exception import RequestHumanTakeover
from module.logger import logger


PLAYCOVER_METHOD = 'playcover'
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


class PlayCoverError(Exception):
    def __init__(self, message, status=None, result=None):
        super().__init__(message)
        self.status = status
        self.result = result


def retry(func):
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (PlayCover):
        """
        reconnect = False
        reconnected = False
        manager_attempted = False
        for trial in range(RETRY_TRIES):
            if reconnect:
                time.sleep(retry_sleep(trial))
                connected, attempted = self.playcover_reconnect(
                    allow_manager=not manager_attempted,
                    force_manager=reconnected,
                )
                manager_attempted = manager_attempted or attempted
                if not connected:
                    continue
                reconnect = False
                reconnected = True

            try:
                return func(self, *args, **kwargs)
            # Can't handle
            except RequestHumanTakeover:
                break
            # MaaTools connection lost
            except (PlayCoverError, OSError, struct.error, ValueError) as e:
                logger.error(e)
                reconnect = True

        logger.critical(f'Retry {func.__name__}() failed')
        self.playcover_release()
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
    screencap_magic = b'SCRN'
    bgr_screencap_magic = b'BGR\x01'
    native_screencap_magic = b'NATV'
    size_magic = b'SIZE'
    touch_magic = b'TUCH'
    touch_sync_magic = b'TSYN'
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
        self.native_screenshot_available = None
        self.bgr_screenshot_available = None

    def connect(self):
        self.disconnect()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect((self.host, self.port))
            self.sock = sock
            self._handshake()
            self.version = self.detect_version()
            if self.version >= 3:
                self.bundle_identifier = self.get_bundle_identifier()
                if self.expected_bundle_identifier \
                        and self.bundle_identifier != self.expected_bundle_identifier:
                    raise PlayCoverError(
                        f'PlayCover MaaTools bundle mismatch: {self.bundle_identifier!r}, '
                        f'expected {self.expected_bundle_identifier!r}'
                    )
            self.max_x, self.max_y = self.get_window_size()
            logger.attr('PlayCover', f'{self.host}:{self.port}')
            logger.attr('PlayCoverMaaToolsVersion', self.version)
            if self.bundle_identifier:
                logger.attr('PlayCoverBundle', self.bundle_identifier)
            logger.attr('PlayCoverWindow', f'{self.max_x}x{self.max_y}')
        except Exception:
            self.disconnect()
            raise
        return self

    def disconnect(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def _send_message(self, magic, payload=b''):
        self.sock.sendall(struct.pack('>H', 4 + len(payload)) + magic + payload)

    def _recv_exact(self, size):
        chunks = []
        received = 0
        while received < size:
            chunk = self.sock.recv(size - received)
            if not chunk:
                raise PlayCoverError(f'Incomplete data received: {received}/{size}')
            chunks.append(chunk)
            received += len(chunk)
        return b''.join(chunks)

    def _handshake(self):
        self.sock.sendall(self.connection_magic)
        response = self._recv_exact(4)
        if response != b'OKAY':
            raise PlayCoverError(f'PlayCover MaaTools handshake failed: {response!r}')

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
                raise PlayCoverError(f'Invalid PlayCover MaaTools bundle length: {size}')
            data = self._recv_exact(size)
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError as e:
            raise PlayCoverError('Invalid PlayCover MaaTools bundle identifier') from e

    def detect_version(self):
        timeout = self.sock.gettimeout()
        self.sock.settimeout(min(timeout or self.timeout, 1))
        try:
            return self.get_version()
        except (OSError, PlayCoverError, struct.error) as e:
            logger.warning(f'Unable to detect PlayCover MaaTools version, disable touch sync: {e}')
            return 0
        finally:
            self.sock.settimeout(timeout)

    def convert(self, x, y):
        x = int(round(int(x) / 1280 * self.max_x))
        y = int(round(int(y) / 720 * self.max_y))
        x = max(0, min(x, self.max_x - 1))
        y = max(0, min(y, self.max_y - 1))
        return x, y

    def send_touch(self, phase, x=0, y=0):
        x, y = self.convert(x, y)
        payload = struct.pack('>BHH', int(phase), x, y)
        with self.lock:
            self._send_message(self.touch_magic, payload)

    def sync_touch(self):
        if self.version < 4:
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
            raise PlayCoverError(f'PlayCover MaaTools touch sync failed: {response!r}')
        return True

    def screenshot_raw(self):
        with self.lock:
            try:
                self._send_message(self.screencap_magic)
                size = struct.unpack('>I', self._recv_exact(4))[0]
                return self._recv_exact(size)
            except socket.timeout:
                raise PlayCoverError(
                    'PlayCover MaaTools screenshot timed out, '
                    'the macOS display may be sleeping, locked, or running without an active monitor'
                )

    def screenshot_bgr_raw(self):
        with self.lock:
            self._send_message(self.bgr_screencap_magic)
            width, height, size = struct.unpack('>III', self._recv_exact(12))
            data = self._recv_exact(size)
        return width, height, data

    def screenshot_native_raw(self):
        with self.lock:
            self._send_message(self.native_screencap_magic)
            width, height, image_format, size = struct.unpack('>II4sI', self._recv_exact(16))
            data = self._recv_exact(size)
        return width, height, image_format, data

    def _log_screenshot_method(self, method):
        if self.screenshot_method != method:
            logger.attr('PlayCoverScreenshot', method)
            self.screenshot_method = method

    @staticmethod
    def _decode_bgr3(width, height, data):
        expected = width * height * 3
        if expected <= 0 or len(data) != expected:
            raise PlayCoverError(
                f'Unexpected PlayCover BGR screenshot size: {len(data)}, '
                f'expected {expected} from {width}x{height}'
            )

        image = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def screenshot_bgr_rgb(self):
        width, height, data = self.screenshot_bgr_raw()
        return self._decode_bgr3(width, height, data)

    def screenshot_native_rgb(self):
        width, height, image_format, data = self.screenshot_native_raw()
        if image_format != b'BGR3':
            raise PlayCoverError(f'Unexpected PlayCover native screenshot format: {image_format!r}')
        return self._decode_bgr3(width, height, data)

    def screenshot_scrn_rgb(self):
        data = self.screenshot_raw()
        expected_rgb = self.max_x * self.max_y * 3
        expected_rgba = self.max_x * self.max_y * 4
        if not data:
            raise PlayCoverError('Empty PlayCover screenshot received')

        if len(data) == expected_rgb:
            image = np.frombuffer(data, dtype=np.uint8).reshape((self.max_y, self.max_x, 3))
        elif len(data) == expected_rgba:
            image = np.frombuffer(data, dtype=np.uint8).reshape((self.max_y, self.max_x, 4))
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        else:
            image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                raise PlayCoverError(
                    f'Unexpected PlayCover screenshot size: {len(data)}, '
                    f'expected {expected_rgb} or {expected_rgba}'
                )
            cv2.cvtColor(image, cv2.COLOR_BGR2RGB, dst=image)

        return image

    @staticmethod
    def _screenshot_error(error):
        if isinstance(error, socket.timeout):
            return (
                'PlayCover MaaTools screenshot timed out, '
                'the macOS display may be sleeping, locked, or running without an active monitor'
            )
        return str(error)

    def _normalize_screenshot(self, image):
        image = np.ascontiguousarray(image, dtype=np.uint8)
        if image.shape[:2] != (720, 1280):
            source_ratio = image.shape[1] / image.shape[0]
            if abs(source_ratio - 16 / 9) > 0.03:
                logger.warning(
                    f'PlayCover screenshot aspect ratio is {image.shape[1]}x{image.shape[0]}, '
                    f'please use a 16:9 PlayCover resolution if recognition is unstable'
                )
            image = cv2.resize(image, (1280, 720), interpolation=cv2.INTER_AREA)
        return image

    def screenshot_rgb(self):
        if self.version >= 5 and self.native_screenshot_available is not False:
            try:
                image = self.screenshot_native_rgb()
                self.native_screenshot_available = True
                self._log_screenshot_method('NATV')
                return self._normalize_screenshot(image)
            except (OSError, PlayCoverError, struct.error, ValueError) as e:
                self.native_screenshot_available = False
                logger.warning(
                    f'Unable to use PlayCover NATV screenshot, fallback to BGR/SCRN: {self._screenshot_error(e)}'
                )

        if self.bgr_screenshot_available is not False:
            try:
                image = self.screenshot_bgr_rgb()
                self.bgr_screenshot_available = True
                self._log_screenshot_method('BGR')
                return self._normalize_screenshot(image)
            except (OSError, PlayCoverError, struct.error, ValueError) as e:
                self.bgr_screenshot_available = False
                logger.warning(
                    f'Unable to use PlayCover BGR screenshot, fallback to SCRN: {self._screenshot_error(e)}'
                )

        image = self.screenshot_scrn_rgb()
        self._log_screenshot_method('SCRN')
        return self._normalize_screenshot(image)


class PlayCoverManagerClient:
    def __init__(self, host=PLAYCOVER_DEFAULT_HOST, port=PLAYCOVER_MANAGER_DEFAULT_PORT, key='', timeout=3):
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
            raise PlayCoverError(
                f'PlayCover manager is not reachable at {self.host}:{self.port}: {e}'
            ) from e
        finally:
            conn.close()

        try:
            result = json.loads(data.decode('utf-8')) if data else {}
        except ValueError:
            result = {'raw': data.decode('utf-8', errors='replace')}

        if response.status >= 400:
            raise PlayCoverError(
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
            raise PlayCoverError(f'Invalid PlayCover manager app list: {result}')
        return apps

    def app_stop(self, bundle_identifier, timeout=10, force=False):
        return self._request('POST', f'{self._app_path(bundle_identifier)}/stop', {
            'timeout': timeout,
            'force': force,
        }, timeout=timeout + 10)

    def maatools_open(
            self, bundle_identifier, port, restart=True, timeout=15, port_timeout=15, fresh='off'
    ):
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
        return self._request('POST', f'{self._app_path(bundle_identifier)}/maatools/open', {
            'port': int(port),
            'restart': restart,
            'timeout': timeout,
            'portTimeout': port_timeout,
            'fresh': fresh,
        }, timeout=request_timeout)


class PlayCover:
    _playcover_hierarchy_warned = False

    def _playcover_connect_client(self, timeout=3, status=None):
        host, port = self.playcover_maatools_address(status=status)
        return MaaToolsClient(
            host=host,
            port=port,
            timeout=timeout,
            expected_bundle_identifier=self.playcover_bundle_identifier(),
        ).connect()

    @cached_property
    def playcover(self):
        manager_status = getattr(self, '_playcover_initial_manager_status', None)
        if hasattr(self, '_playcover_initial_manager_status'):
            del self._playcover_initial_manager_status
        manager_prepared = False

        if self.playcover_manager_configured():
            try:
                if manager_status is None:
                    manager_status = self.playcover_manager_app_status()
                _, port = self.playcover_maatools_address(status=manager_status)
                if not (
                        self._playcover_status_running(manager_status)
                        and self._playcover_status_maatools_reachable(manager_status, port)
                ):
                    logger.info('Prepare PlayCover MaaTools from manager API before connecting')
                    manager_status = self.playcover_manager_ensure_maatools(
                        restart=True,
                        status=manager_status,
                    )
                    manager_prepared = True
            except PlayCoverError as e:
                logger.warning(e)
                if not hasattr(self, '_playcover_maatools_address'):
                    logger.critical('Unable to resolve the PlayCover MaaTools address from manager API')
                    raise RequestHumanTakeover
                logger.info('PlayCover manager API is unavailable, trying the last known MaaTools address')
                manager_status = None

        host, port = self.playcover_maatools_address()
        try:
            return self._playcover_connect_client()
        except Exception as e:
            logger.warning(f'Unable to connect PlayCover MaaTools at {host}:{port}')
            logger.warning(e)

        if manager_status is not None and not manager_prepared:
            try:
                logger.info('PlayCover manager is reachable but MaaTools connection failed, restart once')
                self.playcover_manager_ensure_maatools(
                    restart=True,
                    force=True,
                    status=manager_status,
                )
                return self._playcover_connect_client()
            except Exception as e:
                logger.error(f'Unable to recover PlayCover MaaTools at {host}:{port}')
                logger.error(e)

        raise RequestHumanTakeover

    def playcover_release(self):
        if has_cached_property(self, 'playcover'):
            self.playcover.disconnect()
        del_cached_property(self, 'playcover')
        logger.info('PlayCover MaaTools released')

    def playcover_reconnect(self, allow_manager=True, force_manager=False):
        """
        Returns:
            tuple[bool, bool]: Connection success and whether manager API was attempted.
        """
        self.playcover_release()
        direct_attempted = False

        if not force_manager:
            direct_attempted = True
            try:
                client = self._playcover_connect_client(timeout=1)
                set_cached_property(self, 'playcover', client)
                logger.info('Reconnected PlayCover MaaTools directly')
                return True, False
            except Exception as e:
                logger.warning(f'Unable to reconnect PlayCover MaaTools directly: {e}')

        manager_attempted = False
        if allow_manager and self.playcover_manager_configured():
            manager_attempted = True
            try:
                status = self.playcover_manager_app_status()
                _, port = self.playcover_maatools_address(status=status)
                if (
                        not force_manager
                        and self._playcover_status_running(status)
                        and self._playcover_status_maatools_reachable(status, port)
                ):
                    try:
                        client = self._playcover_connect_client(timeout=1)
                        set_cached_property(self, 'playcover', client)
                        logger.info('Reconnected PlayCover MaaTools at the address reported by manager API')
                        return True, True
                    except Exception as e:
                        logger.warning(f'Unable to connect MaaTools at the address reported by manager API: {e}')
                manager_force = force_manager or (
                    self._playcover_status_running(status)
                    and self._playcover_status_maatools_reachable(status, port)
                )
                logger.info('Recover PlayCover MaaTools from manager API')
                self.playcover_manager_ensure_maatools(
                    restart=True,
                    force=manager_force,
                    status=status,
                )
                client = self._playcover_connect_client()
                set_cached_property(self, 'playcover', client)
                return True, True
            except Exception as e:
                logger.warning(f'Unable to recover PlayCover MaaTools from manager API: {e}')

        if not direct_attempted:
            try:
                client = self._playcover_connect_client(timeout=1)
                set_cached_property(self, 'playcover', client)
                logger.info('Reconnected PlayCover MaaTools directly')
                return True, manager_attempted
            except Exception as e:
                logger.warning(f'Unable to reconnect PlayCover MaaTools directly: {e}')

        return False, manager_attempted

    @cached_property
    def playcover_manager(self):
        host, port = parse_playcover_manager_serial(self.serial)
        logger.attr('PlayCoverManager', f'{host}:{port}')
        return PlayCoverManagerClient(
            host=host,
            port=port,
            key=getattr(self.config, 'PlayCover_ManagerKey', ''),
        )

    def playcover_manager_configured(self):
        return is_playcover_manager_serial(self.serial)

    def playcover_manager_available(self):
        if not self.playcover_manager_configured():
            return False
        try:
            self.playcover_manager_app_status()
            return True
        except PlayCoverError as e:
            logger.warning(e)
            return False

    def playcover_bundle_identifier(self):
        return self.package

    def playcover_manager_app_status(self):
        return self.playcover_manager.app_status(self.playcover_bundle_identifier())

    @staticmethod
    def _playcover_status_maatools_port(status):
        if not isinstance(status, dict):
            return None
        maatools = status.get('maaTools') or {}
        if not isinstance(maatools, dict):
            return None
        try:
            port = int(maatools.get('port') or 0)
        except (TypeError, ValueError):
            return None
        if 1024 <= port <= 65535:
            return port
        return None

    def playcover_maatools_address(self, status=None):
        if not self.playcover_manager_configured():
            return parse_playcover_serial(self.serial)

        if status is not None:
            port = self._playcover_status_maatools_port(status)
            if port is None:
                raise PlayCoverError(f'Invalid MaaTools port in PlayCover app status: {status}')
            host, _ = parse_playcover_manager_serial(self.serial)
            self._playcover_maatools_address = (host, port)
            return self._playcover_maatools_address

        address = getattr(self, '_playcover_maatools_address', None)
        if address is not None:
            return address
        status = getattr(self, '_playcover_initial_manager_status', None)
        if status is not None:
            return self.playcover_maatools_address(status=status)
        return self.playcover_maatools_address(status=self.playcover_manager_app_status())

    @staticmethod
    def _playcover_status_running(status):
        return isinstance(status, dict) and bool(status.get('running'))

    @staticmethod
    def _playcover_status_maatools_reachable(status, port):
        if not isinstance(status, dict):
            return False
        maatools = status.get('maaTools') or {}
        if not isinstance(maatools, dict) or not maatools.get('reachable'):
            return False
        try:
            return int(maatools.get('port') or 0) == int(port)
        except (TypeError, ValueError):
            return False

    def playcover_manager_ensure_maatools(self, restart=True, force=False, status=None):
        if status is None:
            status = self.playcover_manager_app_status()
        _, port = self.playcover_maatools_address(status=status)
        if (
                not force
                and self._playcover_status_running(status)
                and self._playcover_status_maatools_reachable(status, port)
        ):
            logger.info(f'PlayCover MaaTools is reachable on port {port}')
            return status

        logger.info(f'Open PlayCover MaaTools on port {port}')
        try:
            status = self.playcover_manager.maatools_open(
                self.playcover_bundle_identifier(),
                port=port,
                restart=restart,
                fresh='fallback' if restart else 'off',
            )
        except PlayCoverError as e:
            result = e.result if isinstance(e.result, dict) else {}
            self._playcover_log_launch_result(result.get('status'))
            raise
        self._playcover_log_launch_result(status)
        self.playcover_maatools_address(status=status)
        if restart:
            self.playcover_set_need_app_login()
        if not self._playcover_status_running(status):
            raise PlayCoverError(f'PlayCover app is not running after opening MaaTools: {status}')
        if not self._playcover_status_maatools_reachable(status, port):
            raise PlayCoverError(f'PlayCover MaaTools is not reachable after opening: {status}')
        return status

    def _playcover_log_launch_result(self, status):
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

    def playcover_manager_check_app(self, status, action):
        if not self._playcover_status_running(status):
            raise PlayCoverError(f'PlayCover app is not running after {action}: {status}')
        return status

    def playcover_set_need_app_login(self):
        self._playcover_need_app_login = True

    def playcover_need_app_login(self):
        return bool(getattr(self, '_playcover_need_app_login', False))

    def playcover_clear_need_app_login(self):
        self._playcover_need_app_login = False

    def playcover_connect_maatools(self, status=None, restart=True, force=False):
        self.playcover_release()
        status = self.playcover_manager_ensure_maatools(
            restart=restart,
            force=force,
            status=status,
        )
        try:
            client = self._playcover_connect_client(status=status)
        except Exception as e:
            raise PlayCoverError(f'Unable to connect PlayCover MaaTools after manager action: {e}') from e
        set_cached_property(self, 'playcover', client)

    def app_current_playcover(self):
        return self.playcover_bundle_identifier()

    def app_start_playcover(self):
        if not self.playcover_manager_configured():
            logger.info('App start is skipped for PlayCover; manager API is disabled')
            return

        try:
            self.playcover_connect_maatools(restart=True)
            self.playcover_set_need_app_login()
        except PlayCoverError as e:
            logger.error(e)
            raise RequestHumanTakeover

    def app_stop_playcover(self):
        if not self.playcover_manager_configured():
            logger.info('App stop is skipped for PlayCover; manager API is disabled')
            return

        try:
            status = self.playcover_manager.app_stop(self.playcover_bundle_identifier(), timeout=10, force=False)
            self.playcover_release()
            if self._playcover_status_running(status):
                raise PlayCoverError(f'PlayCover app is still running after stop: {status}')
        except PlayCoverError as e:
            logger.error(e)
            raise RequestHumanTakeover

    def app_restart_playcover(self):
        if not self.playcover_manager_configured():
            logger.info('App restart is skipped for PlayCover; manager API is disabled')
            return

        try:
            self.playcover_connect_maatools(restart=True, force=True)
            self.playcover_set_need_app_login()
        except PlayCoverError as e:
            logger.warning(e)
            try:
                status = self.playcover_manager_app_status()
                self.playcover_manager_check_app(status, 'restart')
                client = self._playcover_connect_client(timeout=3, status=status)
                set_cached_property(self, 'playcover', client)
                logger.warning('PlayCover MaaTools became reachable after the manager request timed out')
                self.playcover_set_need_app_login()
            except (PlayCoverError, OSError, struct.error, ValueError) as e:
                logger.error(e)
                raise RequestHumanTakeover

    def app_is_running_playcover(self):
        if self.playcover_manager_configured():
            try:
                return self._playcover_status_running(self.playcover_manager_app_status())
            except PlayCoverError as e:
                logger.warning(e)

        try:
            if has_cached_property(self, 'playcover'):
                self.playcover.get_window_size()
            else:
                client = self._playcover_connect_client(timeout=1)
                client.disconnect()
            return True
        except Exception as e:
            logger.warning(f'PlayCover MaaTools is not reachable: {e}')
            self.playcover_release()
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
        return self.playcover.screenshot_rgb()

    @retry
    def click_playcover(self, x, y):
        down = ensure_time((0.010, 0.020))
        self.playcover.send_touch(0, x, y)
        self.sleep(down)
        self.playcover.send_touch(3, x, y)
        self.playcover.sync_touch()
        self.sleep(0.050 - down)

    @retry
    def long_click_playcover(self, x, y, duration=1.0):
        self.playcover.send_touch(0, x, y)
        self.sleep(duration)
        self.playcover.send_touch(3, x, y)
        self.sleep(0.050)

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
        self.playcover.send_touch(0, first[0], first[1])
        self.sleep(interval)
        for point in points[1:]:
            self.playcover.send_touch(1, point[0], point[1])
            self.sleep(interval)
        last = points[-1]
        self.playcover.send_touch(3, last[0], last[1])
        self.playcover.sync_touch()
        self.sleep(0.050)

    @retry
    def drag_playcover(self, p1, p2, point_random=(-10, -10, 10, 10), hold_duration=0.0):
        p1 = np.array(p1) - random_rectangle_point(point_random)
        p2 = np.array(p2) - random_rectangle_point(point_random)
        points = insert_swipe(p0=p1, p3=p2, speed=20)
        if not points:
            return

        first = points[0]
        self.playcover.send_touch(0, first[0], first[1])
        self.sleep(0.010)
        for point in points[1:]:
            self.playcover.send_touch(1, point[0], point[1])
            self.sleep(0.010)

        self.playcover.send_touch(1, p2[0], p2[1])
        self.sleep(0.140)
        self.playcover.send_touch(1, p2[0], p2[1])
        self.sleep(0.140)

        hold_duration = ensure_time(hold_duration) - 0.28
        if hold_duration > 0:
            self.playcover.send_touch(1, p2[0], p2[1])
            self.sleep(hold_duration)

        self.playcover.send_touch(3, p2[0], p2[1])
        self.sleep(0.050)
