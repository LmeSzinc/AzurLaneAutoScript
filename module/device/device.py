from datetime import datetime, time

from module.device.app import AppControl
from module.device.control import Control
from module.device.screenshot import Screenshot
from module.handler.assets import GET_MISSION
from module.logger import logger


class Device(Screenshot, Control, AppControl):
    def handle_night_commission(self, hour=21, threshold=30):
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

        if GET_MISSION.match(self.image, offset=True):
            logger.info('Night commission appear.')
            self.click(GET_MISSION)
            return True

        return False

    def screenshot(self):
        """
        Returns:
            PIL.Image.Image:
        """
        super().screenshot()
        if self.handle_night_commission():
            super().screenshot()

        return self.image
