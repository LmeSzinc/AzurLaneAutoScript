import typing as t
from functools import wraps

import cv2
import numpy as np
import requests
from adbutils.errors import AdbError

from module.base.decorator import cached_property, del_cached_property
from module.device.method.uiautomator_2 import Uiautomator2, ProcessInfo
from module.device.method.utils import (RETRY_DELAY, RETRY_TRIES, handle_adb_error, PackageNotInstalled)
from module.exception import RequestHumanTakeover
from module.logger import logger


def retry(func):
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (Adb):
        """
        init = None
        for _ in range(RETRY_TRIES):
            try:
                if callable(init):
                    self.sleep(RETRY_DELAY)
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
            # AdbError
            except AdbError as e:
                if handle_adb_error(e):
                    def init():
                        self.adb_reconnect()
                else:
                    break
            # Package not installed
            except PackageNotInstalled as e:
                logger.error(e)

                def init():
                    self.detect_package()
            # DroidCast not running
            # requests.exceptions.ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
            except requests.exceptions.ConnectionError as e:
                logger.error(e)

                def init():
                    self.droidcast_init()
            # Unknown, probably a trucked image
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        logger.critical(f'Retry {func.__name__}() failed')
        raise RequestHumanTakeover

    return retry_wrapper


class DroidCast(Uiautomator2):
    """
    DroidCast, another screenshot method, https://github.com/rayworks/DroidCast

    DroidCast is Added to ALAS for MuMu X support.
    """

    _droidcast_port: int = 0

    @cached_property
    def droidcast_session(self):
        session = requests.Session()
        session.trust_env = False  # Ignore proxy
        self._droidcast_port = self.adb_forward('tcp:53516')
        return session

    def droidcast_url(self, url='/screenshot?format=png'):
        """
        Check APIs from source code:
        https://github.com/rayworks/DroidCast/blob/master/app/src/main/java/com/rayworks/droidcast/Main.java

        Available APIs:
        - /screenshot
            To get JPG screenshots.
        - /screenshot?format=png
            To get PNG screenshots.
        - /screenshot?format=webp
            To get WEBP screenshots.
        - /src
            Websocket to get JPG screenshots.

        Note that /screenshot?format=jpg is unavailable.
        """
        return f'http://127.0.0.1:{self._droidcast_port}{url}'

    def droidcast_init(self):
        logger.hr('Droidcast init')
        self.droidcast_stop()

        logger.info('Pushing DroidCast apk')
        self.adb_push(self.config.DROIDCAST_FILEPATH_LOCAL, self.config.DROIDCAST_FILEPATH_REMOTE)

        logger.info('Starting DroidCast apk')
        # CLASSPATH=/data/local/tmp/DroidCast.apk app_process / com.rayworks.droidcast.Main > /dev/null
        resp = self.u2_shell_background([
            'CLASSPATH=/data/local/tmp/DroidCast.apk',
            'app_process',
            '/',
            'com.rayworks.droidcast.Main',
            '>',
            '/dev/null'
        ])
        logger.info(resp)

        del_cached_property(self, 'droidcast_session')
        _ = self.droidcast_session
        logger.attr('DroidCast', self.droidcast_url())
        self.droidcast_wait_startup()

    @retry
    def screenshot_droidcast(self):
        image = self.droidcast_session.get(self.droidcast_url(), timeout=3).content
        image = np.frombuffer(image, np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    def droidcast_wait_startup(self):
        """
        Wait until DroidCast startup completed.
        """
        for _ in range(6):
            self.sleep(0.5)
            try:
                resp = self.droidcast_session.get(self.droidcast_url('/'), timeout=3)
                # Route `/` is unavailable, but 404 means startup completed
                if resp.status_code == 404:
                    logger.attr('DroidCast', 'online')
                    return True
            except requests.exceptions.ConnectionError:
                logger.attr('DroidCast', 'offline')

        logger.warning('Wait DroidCast startup timeout, assume started')
        return False

    def droidcast_uninstall(self):
        """
        Stop all DroidCast processes and remove DroidCast APK.
        DroidCast has't been installed but a JAVA class call, uninstall is a file delete.
        """
        self.droidcast_stop()
        logger.info('Removing DroidCast')
        self.adb_shell(["rm", self.config.DROIDCAST_FILEPATH_REMOTE])

    def _droidcast_proc(self) -> t.List[ProcessInfo]:
        """
        List all DroidCast processes.
        """
        processes = self.proc_list_uiautomato2()
        processes = [proc for proc in processes if 'com.rayworks.droidcast.Main' in proc.cmdline]
        return processes

    def droidcast_stop(self):
        """
        Stop all DroidCast processes.
        """
        logger.info('Stopping DroidCast')
        for proc in self._droidcast_proc():
            logger.info(f'Kill pid={proc.pid}')
            self.adb_shell(['kill', '-s', 9, proc.pid])
