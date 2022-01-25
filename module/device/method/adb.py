import re

import cv2
import numpy as np
from adbutils.errors import AdbError

from module.device.connection import Connection
from module.device.method.utils import possible_reasons, handle_adb_error, RETRY_TRIES, RETRY_DELAY
from module.exception import ScriptError, RequestHumanTakeover
from module.logger import logger


def retry(func):
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (Adb):
        """
        for _ in range(RETRY_TRIES):
            try:
                return func(self, *args, **kwargs)
            except RequestHumanTakeover:
                # Can't handle
                break
            except ConnectionResetError as e:
                # When adb server was killed
                logger.error(e)
                self.adb_connect(self.serial)
            except AdbError as e:
                if not handle_adb_error(e):
                    break
            except Exception as e:
                # Unknown
                # Probably trucked image
                logger.exception(e)

            self.sleep(RETRY_DELAY)

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

        image = np.fromstring(screenshot, np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
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
        if len(screenshot) < 100:
            logger.warning(f'Unexpected screenshot: {screenshot}')
        raise OSError(f'cannot load screenshot')

    @retry
    def screenshot_adb(self):
        stream = self.adb_shell(['screencap', '-p'], stream=True)

        content = b""
        while True:
            chunk = stream.read(4096)
            if not chunk:
                break
            content += chunk

        return self.__process_screenshot(content)

    @retry
    def click_adb(self, x, y):
        self.adb_shell(['input', 'tap', x, y])

    @retry
    def swipe_adb(self, fx, fy, tx, ty, duration=0.1):
        self.adb_shell(['input', 'swipe', fx, fy, tx, ty, duration])

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
    def app_start_adb(self, package_name):
        result = self.adb_shell([
            'monkey', '-p', package_name, '-c',
            'android.intent.category.LAUNCHER', '1'
        ])
        if 'No activities found' in result:
            # ** No activities found to run, monkey aborted.
            logger.error(result)
            possible_reasons(f'"{package_name}" not found, please check setting Emulator.PackageName')
            raise RequestHumanTakeover
        else:
            # Events injected: 1
            # ## Network stats: elapsed time=4ms (0ms mobile, 0ms wifi, 4ms not connected)
            pass

    @retry
    def app_stop_adb(self, package_name):
        """ Stop one application: am force-stop"""
        self.adb_shell(['am', 'force-stop', package_name])
