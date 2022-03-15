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
    def app_start_wsa_display_0(self, package_name, allow_failure=False):
        """
        Args:
            package_name (str):
            allow_failure (bool):

        Returns:
            bool: If success to start
        """
        self.adb_shell(['svc', 'power', 'stayon', 'true'])
        result = self.adb_shell(
            ['am', 'start', '--display', '0', self.config.Emulator_PackageName +
             '/com.manjuu.azurlane.MainActivity'])
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
    def get_display_id(self):
        try:
            get_dump_sys_display = str(self.adb_shell(['dumpsys', 'display']))
            display_id_list = re.findall(r'systemapp:' + self.config.Emulator_PackageName + ':' + '(.+?)', get_dump_sys_display, re.S)
            display_id = list(set(display_id_list))[0]
            return display_id
        except IndexError:
            return '0'

    @retry
    def wrong_screen_handling(self):
        logger.warning('Game not running on display 0')
        self.adb_shell(['am', 'force-stop', self.config.Emulator_PackageName])

    @retry
    def resize_wsa_display_0(self):
        logger.warning('display 0 should be resized')
        self.adb_shell(['wm', 'size', '1280x720', '-d', '0'])
