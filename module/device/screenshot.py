import os
import time
from collections import deque
from datetime import datetime

from PIL import Image

from module.base.decorator import cached_property
from module.base.timer import Timer, timer
from module.base.utils import get_color
from module.device.method.adb import Adb
from module.device.method.ascreencap import AScreenCap
from module.device.method.uiautomator_2 import Uiautomator2
from module.exception import RequestHumanTakeover
from module.logger import logger


class Screenshot(Adb, Uiautomator2, AScreenCap):
    _screen_size_checked = False
    _screen_black_checked = False
    _minicap_uninstalled = False
    _screenshot_interval_timer = Timer(0.1)
    _last_save_time = {}
    image: Image.Image

    @timer
    def screenshot(self):
        """
        Returns:
            PIL.Image.Image:
        """
        self._screenshot_interval_timer.wait()
        self._screenshot_interval_timer.reset()

        for _ in range(2):
            method = self.config.Emulator_ScreenshotMethod
            if method == 'aScreenCap':
                self.image = self.screenshot_ascreencap()
            elif method == 'uiautomator2':
                self.image = self.screenshot_uiautomator2()
            else:
                self.image = self.screenshot_adb()

            if self.config.Error_SaveError:
                self.screenshot_deque.append({'time': datetime.now(), 'image': self.image})

            if self.check_screen_size() and self.check_screen_black():
                break
            else:
                continue

        return self.image

    @cached_property
    def screenshot_deque(self):
        return deque(maxlen=int(self.config.Error_ScreenshotLength))

    def save_screenshot(self, genre='items', interval=None, to_base_folder=False):
        """Save a screenshot. Use millisecond timestamp as file name.

        Args:
            genre (str, optional): Screenshot type.
            interval (int, float): Seconds between two save. Saves in the interval will be dropped.
            to_base_folder (bool): If save to base folder.

        Returns:
            bool: True if save succeed.
        """
        now = time.time()
        if interval is None:
            interval = self.config.SCREEN_SHOT_SAVE_INTERVAL

        if now - self._last_save_time.get(genre, 0) > interval:
            fmt = 'png'
            file = '%s.%s' % (int(now * 1000), fmt)

            folder = self.config.SCREEN_SHOT_SAVE_FOLDER_BASE if to_base_folder else self.config.SCREEN_SHOT_SAVE_FOLDER
            folder = os.path.join(folder, genre)
            if not os.path.exists(folder):
                os.mkdir(folder)

            file = os.path.join(folder, file)
            self.image.save(file)
            self._last_save_time[genre] = now
            return True
        else:
            self._last_save_time[genre] = now
            return False

    def screenshot_last_save_time_reset(self, genre):
        self._last_save_time[genre] = 0

    def screenshot_interval_set(self, interval):
        interval = max(interval, 0.1)
        if interval != self._screenshot_interval_timer.limit:
            interval = min(interval, 1.0)
            logger.info(f'Screenshot interval set to {interval}s')
            self._screenshot_interval_timer.limit = interval

    def check_screen_size(self):
        """
        Screen size must be 1280x720.
        Take a screenshot before call.
        """
        if self._screen_size_checked:
            return True
        else:
            self._screen_size_checked = True
        # Check screen size
        width, height = self.image.size
        logger.attr('Screen_size', f'{width}x{height}')
        if not (width == 1280 and height == 720):
            logger.critical(f'Resolution not supported: {width}x{height}')
            logger.critical('Please set emulator resolution to 1280x720')
            raise RequestHumanTakeover
        else:
            return True

    def check_screen_black(self):
        if self._screen_black_checked:
            return True
        else:
            self._screen_black_checked = True
        # Check screen color
        # May get a pure black screenshot on some emulators.
        color = get_color(self.image, area=(0, 0, 1280, 720))
        if sum(color) < 1:
            if self.config.Emulator_ScreenshotMethod == 'uiautomator2':
                logger.warning(f'Received pure black screenshots from emulator, color: {color}')
                logger.warning('Uninstall minicap and retry')
                self.uninstall_minicap()
                self._screen_black_checked = False
                return False
            else:
                logger.critical(f'Received pure black screenshots from emulator, color: {color}')
                logger.critical(f'Screenshot method `{self.config.Emulator_ScreenshotMethod}` '
                                f'may not work on emulator `{self.serial}`')
                logger.critical('Please use other screenshot methods')
                raise RequestHumanTakeover
        else:
            return True
