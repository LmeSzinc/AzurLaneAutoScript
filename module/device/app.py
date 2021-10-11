from module.device.connection import Connection
from module.logger import logger
from uiautomator2.exceptions import BaseError
from module.exception import RequestHumanTakeover


class AppControl(Connection):
    def app_is_running(self):
        app = self.device.app_current()
        package = app['package']
        logger.attr('Package_name', package)

        return package == self.config.Emulator_PackageName

    def app_stop(self):
        logger.info(f'App stop: {self.config.Emulator_PackageName}')
        try:
            self.device.app_stop(self.config.Emulator_PackageName)
        except BaseError as e:
            logger.critical(e)
            raise RequestHumanTakeover

    def app_start(self):
        logger.info(f'App start: {self.config.Emulator_PackageName}')
        try:
            self.device.app_start(self.config.Emulator_PackageName)
        except BaseError as e:
            logger.critical(e)
            raise RequestHumanTakeover
