import typing as t
from functools import wraps

import cv2
import numpy as np
import requests
from adbutils.errors import AdbError

from module.base.decorator import Config, cached_property, del_cached_property
from module.base.timer import Timer
from module.device.method.uiautomator_2 import Uiautomator2, ProcessInfo
from module.device.method.utils import (retry_sleep, RETRY_TRIES, handle_adb_error,
                                        ImageTruncated, PackageNotInstalled)
from module.exception import RequestHumanTakeover
from module.logger import logger


class DroidCastVersionIncompatible(Exception):
    pass


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
                    retry_sleep(_)
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
            # DroidCastVersionIncompatible
            except DroidCastVersionIncompatible as e:
                logger.error(e)

                def init():
                    self.droidcast_init()
            # ImageTruncated
            except ImageTruncated as e:
                logger.error(e)

                def init():
                    pass
            # Unknown
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

    @Config.when(DROIDCAST_VERSION='DroidCast')
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

    @Config.when(DROIDCAST_VERSION='DroidCast_raw')
    def droidcast_init(self):
        logger.hr('Droidcast init')
        self.resolution_check_uiautomator2()
        self.droidcast_stop()

        logger.info('Pushing DroidCast apk')
        self.adb_push(self.config.DROIDCAST_RAW_FILEPATH_LOCAL, self.config.DROIDCAST_RAW_FILEPATH_REMOTE)

        logger.info('Starting DroidCast apk')
        # DroidCastS-release-1.1.5.apk
        # CLASSPATH=/data/local/tmp/DroidCastS-release-1.1.5.apk app_process / com.torther.droidcasts.Main > /dev/null
        resp = self.u2_shell_background([
            'CLASSPATH=/data/local/tmp/DroidCastS.apk',
            'app_process',
            '/',
            'com.torther.droidcasts.Main',
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
        self.config.DROIDCAST_VERSION = 'DroidCast'
        image = self.droidcast_session.get(self.droidcast_url(), timeout=3).content
        image = np.frombuffer(image, np.uint8)
        if image is None:
            raise ImageTruncated('Empty image after reading from buffer')
        if image.shape == (1843200,):
            raise DroidCastVersionIncompatible('Requesting screenshots from `DroidCast` but server is `DroidCast_raw`')

        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        if image is None:
            raise ImageTruncated('Empty image after cv2.imdecode')

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        if image is None:
            raise ImageTruncated('Empty image after cv2.cvtColor')

        return image

    @retry
    def screenshot_droidcast_raw(self):
        self.config.DROIDCAST_VERSION = 'DroidCast_raw'
        image = self.droidcast_session.get(self.droidcast_url(), timeout=3).content
        # DroidCast_raw returns a RGB565 bitmap

        try:
            arr = np.frombuffer(image, dtype=np.uint16).reshape((720, 1280))
        except ValueError as e:
            # Try to load as `DroidCast`
            image = np.frombuffer(image, np.uint8)
            if image is not None:
                image = cv2.imdecode(image, cv2.IMREAD_COLOR)
                if image is not None:
                    raise DroidCastVersionIncompatible(
                        'Requesting screenshots from `DroidCast_raw` but server is `DroidCast`')
            # ValueError: cannot reshape array of size 0 into shape (720,1280)
            raise ImageTruncated(str(e))

        # Convert RGB565 to RGB888
        # https://blog.csdn.net/happy08god/article/details/10516871

        # r = (arr & 0b1111100000000000) >> (11 - 3)
        # g = (arr & 0b0000011111100000) >> (5 - 2)
        # b = (arr & 0b0000000000011111) << 3
        # r |= (r & 0b11100000) >> 5
        # g |= (g & 0b11000000) >> 6
        # b |= (b & 0b11100000) >> 5
        # r = r.astype(np.uint8)
        # g = g.astype(np.uint8)
        # b = b.astype(np.uint8)
        # image = cv2.merge([r, g, b])

        # The same as the code above but costs about 5ms instead of 10ms.
        r = cv2.multiply(arr & 0b1111100000000000, 0.00390625).astype(np.uint8)
        g = cv2.multiply(arr & 0b0000011111100000, 0.125).astype(np.uint8)
        b = cv2.multiply(arr & 0b0000000000011111, 8).astype(np.uint8)
        r = cv2.add(r, cv2.multiply(r, 0.03125))
        g = cv2.add(g, cv2.multiply(g, 0.015625))
        b = cv2.add(b, cv2.multiply(b, 0.03125))
        image = cv2.merge([r, g, b])

        return image

    def droidcast_wait_startup(self):
        """
        Wait until DroidCast startup completed.
        """
        timeout = Timer(10).start()
        while 1:
            self.sleep(0.25)
            if timeout.reached():
                break

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
        self.adb_shell(["rm", self.config.DROIDCAST_RAW_FILEPATH_REMOTE])

    def _iter_droidcast_proc(self) -> t.Iterable[ProcessInfo]:
        """
        List all DroidCast processes.
        """
        processes = self.proc_list_uiautomato2()
        for proc in processes:
            if 'com.rayworks.droidcast.Main' in proc.cmdline:
                yield proc
            if 'com.torther.droidcasts.Main' in proc.cmdline:
                yield proc

    def droidcast_stop(self):
        """
        Stop all DroidCast processes.
        """
        logger.info('Stopping DroidCast')
        for proc in self._iter_droidcast_proc():
            logger.info(f'Kill pid={proc.pid}')
            self.adb_shell(['kill', '-s', 9, proc.pid])
