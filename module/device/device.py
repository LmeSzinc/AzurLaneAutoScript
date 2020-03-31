from datetime import datetime, time

from module.base.timer import Timer
from module.device.control import Control
from module.device.screenshot import Screenshot
from module.handler.assets import GET_MISSION
from module.logger import logger


class Device(Screenshot, Control):
    def handle_night_commission(self, hour=21, threshold=5):
        """
        Args:
            hour (int): Hour that night commission refresh.
            threshold (int): Seconds around refresh time.

        Returns:
            bool: If handled.
        """
        now = datetime.now().time()
        if now < time(hour - 1, 59, 60 - threshold):
            return False
        if now > time(hour, 0, threshold):
            return False

        logger.info('Handling night commission')
        wait = Timer(10)
        wait.start()

        while 1:
            super().screenshot()

            if GET_MISSION.appear_on(self.image):
                self.click(GET_MISSION)

            if wait.reached():
                break

        logger.info('Handle night commission finished')
        return True

    def screenshot(self):
        """
        Returns:
            PIL.Image.Image:
        """
        self.handle_night_commission()
        return super().screenshot()
