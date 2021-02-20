from datetime import datetime, timedelta

from module.base.timer import Timer
from module.base.utils import get_color
from module.device.app import AppControl
from module.device.control import Control
from module.device.screenshot import Screenshot
from module.exception import GameStuckError
from module.handler.assets import GET_MISSION
from module.logger import logger
import sys


class Device(Screenshot, Control, AppControl):
    _screen_size_checked = False
    stuck_record = set()
    stuck_timer = Timer(60, count=60).start()
    stuck_timer_long = Timer(300, count=300).start()
    stuck_long_wait_list = ['BATTLE_STATUS_S', 'PAUSE']

    def send_notification(self, title, message):
        if self.config.ENABLE_NOTIFICATIONS and sys.platform == 'win32':
            from notifypy import Notify
            notification = Notify()
            notification.title = title
            notification.message = message
            notification.application_name = "AzurLaneAutoScript"
            notification.icon = "assets/gooey/icon.ico"
            notification.send(block=False)

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
            self.check_screen()
            self._screen_size_checked = True

        return self.image

    def click(self, button, record_check=True):
        self.stuck_record_clear()
        return super().click(button, record_check=record_check)

    def check_screen(self):
        """
        Screen size must be 1280x720.
        Take a screenshot before call.
        """
        # Check screen size
        width, height = self.image.size
        logger.attr('Screen_size', f'{width}x{height}')
        if width == 1280 and height == 720:
            return True
        else:
            logger.warning(f'Not supported screen size: {width}x{height}')
            logger.warning('Alas requires 1280x720')
            logger.hr('Script end')
            exit(1)

        # Check screen color
        # May get a pure black screenshot on some emulators.
        color = get_color(self.image, area=(0, 0, 1280, 720))
        if sum(color) < 1:
            logger.warning('Received a pure black screenshot')
            logger.warning(f'Color: {color}')
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

        if self.config.ENABLE_GAME_STUCK_HANDLER:
            raise GameStuckError(f'Wait too long')

    def disable_stuck_detection(self):
        """
        Disable stuck detection and its handler. Usually uses in semi auto and debugging.
        """
        def empty_function(*arg, **kwargs):
            return False

        self.click_record_check = empty_function
        self.stuck_record_check = empty_function

    def app_start(self):
        super().app_start()
        self.stuck_record_clear()

    def app_stop(self):
        super().app_stop()
        self.stuck_record_clear()
