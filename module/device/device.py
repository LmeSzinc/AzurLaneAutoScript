from datetime import datetime, timedelta

from module.base.timer import Timer
from module.device.app import AppControl
from module.device.control import Control
from module.device.screenshot import Screenshot
from module.handler.assets import GET_MISSION
from module.logger import logger


class Device(Screenshot, Control, AppControl):
    _screen_size_checked = False
    stuck_record = set()
    stuck_timer = Timer(60, count=60).start()
    stuck_timer_long = Timer(300, count=300).start()
    stuck_long_wait_list = ['BATTLE_STATUS_S', 'PAUSE']

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
        self.stuck_record_check()
        super().screenshot()
        if self.handle_night_commission():
            super().screenshot()

        if not self._screen_size_checked:
            self.check_screen_size()
            self._screen_size_checked = True

        return self.image

    def click(self, button):
        self.stuck_record_clear()
        return super().click(button)

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

    def stuck_record_add(self, button):
        self.stuck_record.add(str(button))

    def stuck_record_clear(self):
        self.stuck_record = set()
        self.stuck_timer.reset()
        self.stuck_timer_long.reset()

    def stuck_record_check(self):
        reached = self.stuck_timer.reached()
        reached_long = self.stuck_timer_long.reached()

        if not reached:
            return False
        if not reached_long:
            for button in self.stuck_long_wait_list:
                if button in self.stuck_record:
                    return False

        logger.warning('Wait too long')
        logger.warning(f'Waiting for {self.stuck_record}')
        self.stuck_record_clear()
