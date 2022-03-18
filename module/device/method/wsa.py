import re

from adbutils.errors import AdbError

from module.device.connection import Connection
from module.device.method.utils import possible_reasons, handle_adb_error, RETRY_TRIES, RETRY_DELAY
from module.exception import RequestHumanTakeover
from module.logger import logger


def retry(func):
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
                    self.adb_disconnect(self.serial)
                    self.adb_connect(self.serial)
            # AdbError
            except AdbError as e:
                if handle_adb_error(e):
                    def init():
                        self.adb_disconnect(self.serial)
                        self.adb_connect(self.serial)
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


class WSA(Connection):

    @retry
    def app_start_wsa(self, package_name, display, allow_failure=False):
        """
        Args:
            package_name (str):
            display (int):
            allow_failure (bool):

        Returns:
            bool: If success to start
        """

        self.adb_shell(['svc', 'power', 'stayon', 'true'])
        activity_name = self.get_main_activity_name(package_name=package_name)
        result = self.adb_shell(
            ['am', 'start', '--display', display, package_name +
             '/' + activity_name])
        if 'No activities found' in result:
            # ** No activities found to run, monkey aborted.
            if allow_failure:
                return False
            else:
                logger.error(result)
                possible_reasons(f'"{package_name}" not found, please check setting Emulator.PackageName')
                raise RequestHumanTakeover
        else:
            # Events injected: 1
            # ## Network stats: elapsed time=4ms (0ms mobile, 0ms wifi, 4ms not connected)
            return True

    @retry
    def get_main_activity_name(self, package_name):
        try:
            output = self.adb_shell(['dumpsys', 'package', package_name])
            _activityRE = re.compile(
                r'\w+ ' + package_name + r'/(?P<activity>[^/\s]+) filter'
            )
            ms = _activityRE.finditer(output)
            ret = next(ms).group('activity')
            return ret
        except StopIteration:
            raise RequestHumanTakeover("Couldn't get activity name, please check setting Emulator.PackageName")

    @retry
    def get_display_id(self):
        """
            Returns:
                0: Could not find
                int: Display id of the game
        """
        try:
            get_dump_sys_display = str(self.adb_shell(['dumpsys', 'display']))
            display_id_list = re.findall(r'systemapp:' + self.config.Emulator_PackageName + ':' + '(.+?)', get_dump_sys_display, re.S)
            display_id = int(display_id_list[0])
            return display_id
        except IndexError:
            return 0  # When game running on display 0, its display id could not be found

    @retry
    def display_resize_wsa(self, display):
        logger.warning('display ' + str(display) + ' should be resized')
        self.adb_shell(['wm', 'size', '1280x720', '-d', str(display)])
