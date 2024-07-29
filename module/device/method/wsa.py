import re
from functools import wraps

from adbutils.errors import AdbError

from module.device.connection import Connection
from module.device.method.utils import (PackageNotInstalled, RETRY_TRIES, handle_adb_error, handle_unknown_host_service,
                                        retry_sleep)
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
            # Unknown, probably a trucked image
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        logger.critical(f'Retry {func.__name__}() failed')
        raise RequestHumanTakeover

    return retry_wrapper


class WSA(Connection):

    @retry
    def app_current_wsa(self):
        """
        Returns:
            str: Package name.

        Raises:
            OSError
        """
        # try: adb shell dumpsys activity top
        _activityRE = re.compile(
            r'ACTIVITY (?P<package>[^\s]+)/(?P<activity>[^/\s]+) \w+ pid=(?P<pid>\d+)'
        )
        output = self.adb_shell(['dumpsys', 'activity', 'top'])
        ms = _activityRE.finditer(output)
        ret = None
        for m in ms:
            ret = m.group('package')
            if ret == self.package:
                return ret
        if ret:  # get last result
            return ret
        raise OSError("Couldn't get focused app")

    @retry
    def app_start_wsa(self, package_name=None, display=0):
        """
        Args:
            package_name (str):
            display (int):

        Returns:
            bool: If success to start
        """
        if not package_name:
            package_name = self.package
        self.adb_shell(['svc', 'power', 'stayon', 'true'])
        activity_name = self.get_main_activity_name(package_name=package_name)
        result = self.adb_shell(['am', 'start', '--display', display, f'{package_name}/{activity_name}'])
        if 'Activity not started' in result or 'does not exist' in result:
            # Starting: Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] pkg=xxx }
            # Error: Activity not started, unable to resolve Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10000000 pkg=xxx }

            # Starting: Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] cmp=com.bilibili.azurlane/xxx }
            # Error type 3
            # Error: Activity class {com.bilibili.azurlane/com.manjuu.azurlane.MainAct} does not exist.
            logger.error(result)
            raise PackageNotInstalled(package_name)
        else:
            # Starting: Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] cmp=com.bilibili.azurlane/com.manjuu.azurlane.MainActivity }
            return True

    @retry
    def get_main_activity_name(self, package_name=None):
        if not package_name:
            package_name = self.package
        try:
            output = self.adb_shell(['dumpsys', 'package', package_name])
            _activityRE = re.compile(
                r'\w+ ' + package_name + r'/(?P<activity>[^/\s]+) filter'
            )
            ms = _activityRE.finditer(output)
            ret = next(ms).group('activity')
            return ret
        except StopIteration:
            raise PackageNotInstalled(package_name)

    @retry
    def get_display_id(self):
        """
            Returns:
                0: Could not find
                int: Display id of the game
        """
        try:
            get_dump_sys_display = str(self.adb_shell(['dumpsys', 'display']))
            display_id_list = re.findall(r'systemapp:' + self.package + ':' + '(.+?)', get_dump_sys_display, re.S)
            display_id = int(display_id_list[0])
            return display_id
        except IndexError:
            return 0  # When game running on display 0, its display id could not be found

    @retry
    def display_resize_wsa(self, display):
        logger.warning('display ' + str(display) + ' should be resized')
        self.adb_shell(['wm', 'size', '1280x720', '-d', str(display)])
