from module.device.method.adb import Adb
from module.device.method.uiautomator_2 import Uiautomator2
from module.logger import logger


class AppControl(Adb, Uiautomator2):
    def app_is_running(self) -> bool:
        method = self.config.Emulator_ControlMethod
        if method == 'uiautomator2' or method == 'minitouch':
            package = self.app_current_uiautomator2()
        else:
            package = self.app_current_adb()

        logger.attr('Package_name', package)
        return package == self.config.Emulator_PackageName

    def app_start(self):
        package = self.config.Emulator_PackageName
        method = self.config.Emulator_ControlMethod
        logger.info(f'App start: {package}')
        if method == 'uiautomator2' or method == 'minitouch':
            self.app_start_uiautomator2(package)
        else:
            self.app_start_adb(package)

    def app_stop(self):
        package = self.config.Emulator_PackageName
        method = self.config.Emulator_ControlMethod
        logger.info(f'App stop: {package}')
        if method == 'uiautomator2' or method == 'minitouch':
            self.app_stop_uiautomator2(package)
        else:
            self.app_stop_adb(package)
