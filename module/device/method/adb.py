import re
from functools import wraps

import cv2
import numpy as np
from adbutils.errors import AdbError
from lxml import etree

from module.device.connection import Connection
from module.device.method.utils import (RETRY_DELAY, RETRY_TRIES,
                                        handle_adb_error, PackageNotInstalled)
from module.exception import RequestHumanTakeover, ScriptError
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
            # Unknown, probably a trucked image
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        logger.critical(f'Retry {func.__name__}() failed')
        raise RequestHumanTakeover

    return retry_wrapper


class Adb(Connection):
    __screenshot_method = [0, 1, 2]
    __screenshot_method_fixed = [0, 1, 2]

    @staticmethod
    def __load_screenshot(screenshot, method):
        if method == 0:
            pass
        elif method == 1:
            screenshot = screenshot.replace(b'\r\n', b'\n')
        elif method == 2:
            screenshot = screenshot.replace(b'\r\r\n', b'\n')
        else:
            raise ScriptError(f'Unknown method to load screenshots: {method}')

        # fix compatibility issues for adb screencap decode problem when the data is from vmos pro
        # When use adb screencap for a screenshot from vmos pro, there would be a header more than that from emulator
        # which would cause image decode problem. So i check and remove the header there.
        if screenshot.startswith(b'long long=8 fun*=10\n'):
            screenshot = screenshot.replace(b'long long=8 fun*=10\n', b'', 1)

        image = np.frombuffer(screenshot, np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        if image is None:
            raise OSError('Empty image')
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    def __process_screenshot(self, screenshot):
        for method in self.__screenshot_method_fixed:
            try:
                result = self.__load_screenshot(screenshot, method=method)
                self.__screenshot_method_fixed = [method] + self.__screenshot_method
                return result
            except OSError:
                continue

        self.__screenshot_method_fixed = self.__screenshot_method
        if len(screenshot) < 500:
            logger.warning(f'Unexpected screenshot: {screenshot}')
        raise OSError(f'cannot load screenshot')

    @retry
    def screenshot_adb(self):
        content = self.adb_shell(['screencap', '-p'], stream=True)

        return self.__process_screenshot(content)

    @retry
    def screenshot_adb_nc(self):
        data = self.adb_shell_nc(['screencap'])
        if len(data) < 500:
            logger.warning(f'Unexpected screenshot: {data}')

        # Load data
        header = np.frombuffer(data[0:12], dtype=np.uint32)
        channel = 4  # screencap sends an RGBA image
        width, height, _ = header  # Usually to be 1280, 720, 1

        image = np.frombuffer(data, dtype=np.uint8)
        shape = image.shape[0]
        image = image[shape - width * height * channel:].reshape(height, width, channel)
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        return image

    @retry
    def click_adb(self, x, y):
        self.adb_shell(['input', 'tap', x, y])

    @retry
    def swipe_adb(self, p1, p2, duration=0.1):
        duration = int(duration * 1000)
        self.adb_shell(['input', 'swipe', *p1, *p2, duration])

    @retry
    def app_current_adb(self):
        """
        Copied from uiautomator2

        Returns:
            str: Package name.

        Raises:
            OSError

        For developer:
            Function reset_uiautomator need this function, so can't use jsonrpc here.
        """
        # Related issue: https://github.com/openatx/uiautomator2/issues/200
        # $ adb shell dumpsys window windows
        # Example output:
        #   mCurrentFocus=Window{41b37570 u0 com.incall.apps.launcher/com.incall.apps.launcher.Launcher}
        #   mFocusedApp=AppWindowToken{422df168 token=Token{422def98 ActivityRecord{422dee38 u0 com.example/.UI.play.PlayActivity t14}}}
        # Regexp
        #   r'mFocusedApp=.*ActivityRecord{\w+ \w+ (?P<package>.*)/(?P<activity>.*) .*'
        #   r'mCurrentFocus=Window{\w+ \w+ (?P<package>.*)/(?P<activity>.*)\}')
        _focusedRE = re.compile(
            r'mCurrentFocus=Window{.*\s+(?P<package>[^\s]+)/(?P<activity>[^\s]+)\}'
        )
        m = _focusedRE.search(self.adb_shell(['dumpsys', 'window', 'windows']))
        if m:
            return m.group('package')

        # try: adb shell dumpsys activity top
        _activityRE = re.compile(
            r'ACTIVITY (?P<package>[^\s]+)/(?P<activity>[^/\s]+) \w+ pid=(?P<pid>\d+)'
        )
        output = self.adb_shell(['dumpsys', 'activity', 'top'])
        ms = _activityRE.finditer(output)
        ret = None
        for m in ms:
            ret = m.group('package')
        if ret:  # get last result
            return ret
        raise OSError("Couldn't get focused app")

    @retry
    def app_start_adb(self, package_name=None, allow_failure=False):
        """
        Args:
            package_name (str):
            allow_failure (bool):

        Returns:
            bool: If success to start
        """
        if not package_name:
            package_name = self.package
        result = self.adb_shell([
            'monkey', '-p', package_name, '-c',
            'android.intent.category.LAUNCHER', '1'
        ])
        if 'No activities found' in result:
            # ** No activities found to run, monkey aborted.
            if allow_failure:
                return False
            else:
                logger.error(result)
                raise PackageNotInstalled(package_name)
        else:
            # Events injected: 1
            # ## Network stats: elapsed time=4ms (0ms mobile, 0ms wifi, 4ms not connected)
            return True

    @retry
    def app_stop_adb(self, package_name=None):
        """ Stop one application: am force-stop"""
        if not package_name:
            package_name = self.package
        self.adb_shell(['am', 'force-stop', package_name])

    @retry
    def dump_hierarchy_adb(self, temp: str = '/data/local/tmp/hierarchy.xml') -> etree._Element:
        """
        Args:
            temp (str): Temp file store on emulator.

        Returns:
            etree._Element:
        """
        # Remove existing file
        # self.adb_shell(['rm', '/data/local/tmp/hierarchy.xml'])

        # Dump hierarchy
        for _ in range(2):
            response = self.adb_shell(['uiautomator', 'dump', '--compressed', temp])
            if 'hierchary' in response:
                # UI hierchary dumped to: /data/local/tmp/hierarchy.xml
                break
            else:
                # <None>
                # Must kill uiautomator2
                self.app_stop_adb('com.github.uiautomator')
                self.app_stop_adb('com.github.uiautomator.test')
                continue

        # Read from device
        content = b''
        for chunk in self.adb.sync.iter_content(temp):
            if chunk:
                content += chunk
            else:
                break

        # Parse with lxml
        hierarchy = etree.fromstring(content)
        return hierarchy
