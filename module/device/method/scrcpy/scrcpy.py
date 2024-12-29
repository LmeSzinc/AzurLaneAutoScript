import socket
import time
from functools import wraps

import numpy as np
from adbutils.errors import AdbError, AdbTimeout

import module.device.method.scrcpy.const as const
from module.base.utils import random_rectangle_point
from module.device.method.minitouch import insert_swipe
from module.device.method.scrcpy.core import ScrcpyCore, ScrcpyError
from module.device.method.uiautomator_2 import Uiautomator2
from module.device.method.utils import RETRY_TRIES, handle_adb_error, handle_unknown_host_service, retry_sleep
from module.exception import RequestHumanTakeover
from module.logger import logger


def retry(func):
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (ScrcpyCore):
        """
        init = None
        for _ in range(RETRY_TRIES):
            try:
                if callable(init):
                    time.sleep(retry_sleep(_))
                    init()
                return func(self, *args, **kwargs)
            # Can't handle
            except RequestHumanTakeover:
                break
            # When adb server was killed
            except ConnectionResetError as e:
                logger.error(e)

                def init():
                    self.adb_reconnect()
            # Emulator closed
            except ConnectionAbortedError as e:
                logger.error(e)

                def init():
                    self.adb_reconnect()
            # ScrcpyError
            except ScrcpyError as e:
                logger.error(e)

                def init():
                    self.scrcpy_init()
            # AdbTimeout
            # socket.timeout
            except (AdbTimeout, socket.timeout) as e:
                logger.error(e)

                def init():
                    self.scrcpy_init()
            # AdbError
            except AdbError as e:
                if handle_adb_error(e):
                    def init():
                        self.adb_reconnect()
                elif handle_unknown_host_service(e):
                    def init():
                        self.adb_start_server()
                        self.adb_reconnect()
                else:
                    break
            # Unknown, probably a trucked image
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        logger.critical(f'Retry {func.__name__}() failed')
        raise RequestHumanTakeover

    return retry_wrapper


class Scrcpy(ScrcpyCore, Uiautomator2):
    def _scrcpy_resolution_check(self):
        if not self._scrcpy_alive:
            with self._scrcpy_control_socket_lock:
                self.resolution_check_uiautomator2()

    @retry
    def screenshot_scrcpy(self):
        self._scrcpy_resolution_check()
        self.scrcpy_ensure_running()

        with self._scrcpy_control_socket_lock:
            # Wait new frame
            now = time.time()
            while 1:
                time.sleep(0.001)
                thread = self._scrcpy_stream_loop_thread
                if thread is None or not thread.is_alive():
                    raise ScrcpyError('_scrcpy_stream_loop_thread died')
                if self._scrcpy_last_frame_time > now:
                    screenshot = self._scrcpy_last_frame.copy()
                    return screenshot

    @retry
    def click_scrcpy(self, x, y):
        self.scrcpy_ensure_running()

        with self._scrcpy_control_socket_lock:
            self._scrcpy_control.touch(x, y, const.ACTION_DOWN)
            self._scrcpy_control.touch(x, y, const.ACTION_UP)
            self.sleep(0.05)

    @retry
    def long_click_scrcpy(self, x, y, duration=1.0):
        self.scrcpy_ensure_running()

        with self._scrcpy_control_socket_lock:
            self._scrcpy_control.touch(x, y, const.ACTION_DOWN)
            self.sleep(duration)
            self._scrcpy_control.touch(x, y, const.ACTION_UP)
            self.sleep(0.05)

    @retry
    def swipe_scrcpy(self, p1, p2):
        self.scrcpy_ensure_running()

        with self._scrcpy_control_socket_lock:
            # Unlike minitouch, scrcpy swipes needs to be continuous
            # So 5 times smother
            points = insert_swipe(p0=p1, p3=p2, speed=4, min_distance=2)
            self._scrcpy_control.touch(*p1, const.ACTION_DOWN)

            for point in points[1:-1]:
                self._scrcpy_control.touch(*point, const.ACTION_MOVE)
                self.sleep(0.002)

            self._scrcpy_control.touch(*p2, const.ACTION_MOVE)
            self._scrcpy_control.touch(*p2, const.ACTION_UP)
            self.sleep(0.05)

    @retry
    def drag_scrcpy(self, p1, p2, point_random=(-10, -10, 10, 10)):
        self.scrcpy_ensure_running()

        with self._scrcpy_control_socket_lock:
            p1 = np.array(p1) - random_rectangle_point(point_random)
            p2 = np.array(p2) - random_rectangle_point(point_random)
            points = insert_swipe(p0=p1, p3=p2, speed=4, min_distance=2)

            self._scrcpy_control.touch(*p1, const.ACTION_DOWN)

            for point in points[1:-1]:
                self._scrcpy_control.touch(*point, const.ACTION_MOVE)
                self.sleep(0.002)

            # Hold 280ms
            for _ in range(int(0.14 // 0.002) * 2):
                self._scrcpy_control.touch(*p2, const.ACTION_MOVE)
                self.sleep(0.002)

            self._scrcpy_control.touch(*p2, const.ACTION_UP)
            self.sleep(0.05)
