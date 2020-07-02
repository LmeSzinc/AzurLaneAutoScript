from datetime import datetime, timedelta

from module.device.app import AppControl
from module.device.control import Control
from module.device.screenshot import Screenshot
from module.handler.assets import GET_MISSION
from module.logger import logger


class Device(Screenshot, Control, AppControl):
    _screen_size_checked = False

    def handle_night_commission(self, hour=21, threshold=30):
        """
        Args:
            hour (int): Hour that night commission refresh.
            threshold (int): Seconds around refresh time.

        Returns:
            bool: If handled.
        """
        update = self.config.get_server_last_update(since=(hour,))
        now = datetime.now().time()
        if now < (update - timedelta(seconds=threshold)).time():
            return False
        if now > (update + timedelta(seconds=threshold)).time():
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

        if not self._screen_size_checked:
            self.check_screen_size()
            self._screen_size_checked = True

        return self.image

    def check_screen_size(self):
        """
        Screen size must be 1280x720, if not exit.
        Take a screenshot before call.
        """
        width, height = self.image.size
        if height > width:
            width, height = height, width

        logger.attr('Screen_size', f'{width}x{height}')

        if width == 1280 and height == 720:
            return True
        else:
            logger.warning(f'Not supported screen size: {width}x{height}')
            logger.warning('Alas requires 1280x720')
            logger.hr('Script end')
            exit(1)