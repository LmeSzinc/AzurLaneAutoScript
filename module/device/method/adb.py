import re
import time
from functools import wraps

import cv2
import numpy as np
from adbutils.errors import AdbError
from lxml import etree

from module.base.decorator import Config
from module.config.server import DICT_PACKAGE_TO_ACTIVITY
from module.device.connection import Connection
from module.device.method.utils import (ImageTruncated, PackageNotInstalled, RETRY_TRIES, handle_adb_error,
                                        handle_unknown_host_service, remove_prefix, retry_sleep)
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
                elif handle_unknown_host_service(e):
                    def init():
                        self.adb_start_server()
                        self.adb_reconnect()
                else:
                    break
            # Package not installed
            except PackageNotInstalled as e:
                logger.error(e)

                def init():
                    self.detect_package()
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


def load_screencap(data):
    """
    Args:
        data: Raw data from `screencap`

    Returns:
        np.ndarray:
    """
    # Load data
    header = np.frombuffer(data[0:12], dtype=np.uint32)
    channel = 4  # screencap sends an RGBA image
    width, height, _ = header  # Usually to be 1280, 720, 1

    image = np.frombuffer(data, dtype=np.uint8)
    if image is None:
        raise ImageTruncated('Empty image after reading from buffer')

    try:
        image = image[-int(width * height * channel):].reshape(height, width, channel)
    except ValueError as e:
        # ValueError: cannot reshape array of size 0 into shape (720,1280,4)
        raise ImageTruncated(str(e))

    image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    if image is None:
        raise ImageTruncated('Empty image after cv2.cvtColor')

    return image


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
        screenshot = remove_prefix(screenshot, b'long long=8 fun*=10\n')

        image = np.frombuffer(screenshot, np.uint8)
        if image is None:
            raise ImageTruncated('Empty image after reading from buffer')

        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        if image is None:
            raise ImageTruncated('Empty image after cv2.imdecode')

        cv2.cvtColor(image, cv2.COLOR_BGR2RGB, dst=image)
        if image is None:
            raise ImageTruncated('Empty image after cv2.cvtColor')

        return image

    def __process_screenshot(self, screenshot):
        for method in self.__screenshot_method_fixed:
            try:
                result = self.__load_screenshot(screenshot, method=method)
                self.__screenshot_method_fixed = [method] + self.__screenshot_method
                return result
            except (OSError, ImageTruncated):
                continue

        self.__screenshot_method_fixed = self.__screenshot_method
        if len(screenshot) < 500:
            logger.warning(f'Unexpected screenshot: {screenshot}')
        raise OSError(f'cannot load screenshot')

    @retry
    @Config.when(DEVICE_OVER_HTTP=False)
    def screenshot_adb(self):
        data = self.adb_shell(['screencap', '-p'], stream=True)
        if len(data) < 500:
            logger.warning(f'Unexpected screenshot: {data}')

        return self.__process_screenshot(data)

    @retry
    @Config.when(DEVICE_OVER_HTTP=True)
    def screenshot_adb(self):
        data = self.adb_shell(['screencap'], stream=True)
        if len(data) < 500:
            logger.warning(f'Unexpected screenshot: {data}')

        return load_screencap(data)

    @retry
    def screenshot_adb_nc(self):
        data = self.adb_shell_nc(['screencap'])
        if len(data) < 500:
            logger.warning(f'Unexpected screenshot: {data}')

        return load_screencap(data)

    @retry
    def click_adb(self, x, y):
        start = time.time()
        self.adb_shell(['input', 'tap', x, y])
        if time.time() - start <= 0.05:
            self.sleep(0.05)

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
    def _app_start_adb_monkey(self, package_name=None, allow_failure=False):
        """
        Args:
            package_name (str):
            allow_failure (bool):

        Returns:
            bool: If success to start

        Raises:
            PackageNotInstalled:
        """
        if not package_name:
            package_name = self.package
        result = self.adb_shell([
            'monkey', '-p', package_name, '-c',
            'android.intent.category.LAUNCHER', '--pct-syskeys', '0', '1'
        ])
        if 'No activities found' in result:
            # ** No activities found to run, monkey aborted.
            if allow_failure:
                return False
            else:
                logger.error(result)
                raise PackageNotInstalled(package_name)
        elif 'inaccessible' in result:
            # /system/bin/sh: monkey: inaccessible or not found
            return False
        else:
            # Events injected: 1
            # ## Network stats: elapsed time=4ms (0ms mobile, 0ms wifi, 4ms not connected)
            return True

    @retry
    def _app_start_adb_am(self, package_name=None, activity_name=None, allow_failure=False):
        """
        Args:
            package_name (str):
            activity_name (str):
            allow_failure (bool):

        Returns:
            bool: If success to start

        Raises:
            PackageNotInstalled:
        """
        if not package_name:
            package_name = self.package
        if not activity_name:
            result = self.adb_shell(['dumpsys', 'package', package_name])
            res = re.search(r'android.intent.action.MAIN:\s+\w+ ([\w.\/]+) filter \w+\s+'
                            r'.*\s+Category: "android.intent.category.LAUNCHER"',
                            result)
            if res:
                # com.bilibili.azurlane/com.manjuu.azurlane.MainActivity
                activity_name = res.group(1)
                try:
                    activity_name = activity_name.split('/')[-1]
                except IndexError:
                    logger.error(f'No activity name from {activity_name}')
                    return False
            else:
                if allow_failure:
                    return False
                else:
                    logger.error(result)
                    raise PackageNotInstalled(package_name)

        cmd = ['am', 'start', '-a', 'android.intent.action.MAIN', '-c',
               'android.intent.category.LAUNCHER', '-n', f'{package_name}/{activity_name}']
        if self.is_local_network_device and self.is_waydroid:
            cmd += ['--windowingMode', '4']
        ret = self.adb_shell(cmd)
        # Invalid activity
        # Starting: Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] cmp=... }
        # Error type 3
        # Error: Activity class {.../...} does not exist.
        if 'Error: Activity class' in ret:
            if allow_failure:
                return False
            else:
                logger.error(ret)
                return False
        # Already running
        # Warning: Activity not started, intent has been delivered to currently running top-most instance.
        if 'Warning: Activity not started' in ret:
            logger.info('App activity is already started')
            return True
        # Starting: Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] cmp=com.YoStarEN.AzurLane/com.manjuu.azurlane.MainActivity }
        # java.lang.SecurityException: Permission Denial: starting Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10000000 cmp=com.YoStarEN.AzurLane/com.manjuu.azurlane.MainActivity } from null (pid=5140, uid=2000) not exported from uid 10064
        #         at android.os.Parcel.readException(Parcel.java:1692)
        #         at android.os.Parcel.readException(Parcel.java:1645)
        #         at android.app.ActivityManagerProxy.startActivityAsUser(ActivityManagerNative.java:3152)
        #         at com.android.commands.am.Am.runStart(Am.java:643)
        #         at com.android.commands.am.Am.onRun(Am.java:394)
        #         at com.android.internal.os.BaseCommand.run(BaseCommand.java:51)
        #         at com.android.commands.am.Am.main(Am.java:124)
        #         at com.android.internal.os.RuntimeInit.nativeFinishInit(Native Method)
        #         at com.android.internal.os.RuntimeInit.main(RuntimeInit.java:290)
        if 'Permission Denial' in ret:
            if allow_failure:
                return False
            else:
                logger.error(ret)
                logger.error('Permission Denial while starting app, probably because activity invalid')
                return False
        # Success
        # Starting: Intent...
        return True

    # No @retry decorator since _app_start_adb_am and _app_start_adb_monkey have @retry already
    # @retry
    def app_start_adb(self, package_name=None, activity_name=None, allow_failure=False):
        """
        Args:
            package_name (str):
                If None, to get from config
            activity_name (str):
                If None, to get from DICT_PACKAGE_TO_ACTIVITY
                If still None, launch from monkey
                If monkey failed, fetch activity name and launch from am
            allow_failure (bool):
                True for no PackageNotInstalled raising, just return False

        Returns:
            bool: If success to start

        Raises:
            PackageNotInstalled:
        """
        if not package_name:
            package_name = self.package
        if not activity_name:
            activity_name = DICT_PACKAGE_TO_ACTIVITY.get(package_name)

        if activity_name:
            if self._app_start_adb_am(package_name, activity_name, allow_failure):
                return True
        if self._app_start_adb_monkey(package_name, allow_failure):
            return True
        if self._app_start_adb_am(package_name, activity_name, allow_failure):
            return True

        logger.error('app_start_adb: All trials failed')
        return False

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
