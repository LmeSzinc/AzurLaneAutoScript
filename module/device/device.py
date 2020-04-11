from datetime import datetime, time

from module.base.timer import Timer
from module.device.app import AppControl
from module.device.control import Control
from module.device.screenshot import Screenshot
from module.handler.assets import GET_MISSION
from module.logger import logger


class Device(Screenshot, Control, AppControl):
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
                super().click(GET_MISSION)

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

    def click(self, button, adb=False):
        self.handle_night_commission()
        return super().click(button, adb=adb)

    def swipe(self, vector, box=(123, 159, 1193, 628), random_range=(0, 0, 0, 0), padding=15, duration=(0.1, 0.2)):
        self.handle_night_commission()
        return super().swipe(vector=vector, box=box, random_range=random_range, padding=padding, duration=duration)

