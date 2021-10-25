from datetime import datetime

from module.base.timer import Timer
from module.base.utils import get_color
from module.config.utils import get_server_next_update
from module.device.app import AppControl
from module.device.control import Control
from module.device.screenshot import Screenshot
from module.exception import GameStuckError, RequestHumanTakeover
from module.handler.assets import GET_MISSION
from module.logger import logger


class Device(Screenshot, Control, AppControl):
    _screen_size_checked = False
    stuck_record = set()
    stuck_timer = Timer(60, count=60).start()
    stuck_timer_long = Timer(300, count=300).start()
    stuck_long_wait_list = ['BATTLE_STATUS_S', 'PAUSE', 'LOGIN_CHECK']

    def handle_night_commission(self, daily_trigger='21:00', threshold=30):
        """
        Args:
            daily_trigger (int): Time for commission refresh.
            threshold (int): Seconds around refresh time.

        Returns:
            bool: If handled.
        """
        update = get_server_next_update(daily_trigger=daily_trigger)
        now = datetime.now()
        diff = (update.timestamp() - now.timestamp()) % 86400
        if threshold < diff < 86400 - threshold:
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
        if not (width == 1280 and height == 720):
            logger.critical(f'Resolution not supported: {width}x{height}')
            logger.critical('Please set emulator resolution to 1280x720')
            raise RequestHumanTakeover

        # Check screen color
        # May get a pure black screenshot on some emulators.
        color = get_color(self.image, area=(0, 0, 1280, 720))
        if sum(color) < 1:
            logger.critical(f'Received pure black screenshots from emulator, color: {color}')
            logger.critical(f'Screenshot method `{self.config.Emulator_ScreenshotMethod}` '
                            f'may not work on emulator `{self.serial}`')
            logger.critical('Please use other screenshot methods')
            raise RequestHumanTakeover

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

        raise GameStuckError(f'Wait too long')

    def disable_stuck_detection(self):
        """
        Disable stuck detection and its handler. Usually uses in semi auto and debugging.
        """
        logger.info('Disable stuck detection')

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
