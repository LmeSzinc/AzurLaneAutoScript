import cv2
from scipy import signal

from module.base.timer import Timer
from module.base.utils import rgb2gray
from module.logger import logger
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_state import COMBAT_AUTO, COMBAT_PAUSE, COMBAT_SPEED_2X


class CombatState(UI):
    _combat_click_interval = Timer(2, count=4)
    _combat_auto_checked = False
    _combat_2x_checked = False

    def is_combat_executing(self) -> bool:
        appear = self.appear(COMBAT_PAUSE)
        if appear:
            if COMBAT_PAUSE.button_offset[0] <= 5:
                return True

        return False

    def _is_combat_button_active(self, button):
        image = rgb2gray(self.image_crop(button))
        lines = cv2.reduce(image, 1, cv2.REDUCE_AVG).flatten()
        # [122 122 122 182 141 127 139 135 130 135 136 141 147 149 149 150 147 145
        #  148 150 150 150 150 150 144 138 134 141 136 133 173 183 130 128 127 126]
        parameters = {
            # Border is about 188-190
            'height': 96,
            # Background is about 120-122
            'prominence': 35,
            'width': (0, 7),
            'distance': 7,
        }
        peaks, _ = signal.find_peaks(lines, **parameters)
        count = len(peaks)
        if count == 0:
            return False
        elif count == 2:
            return True
        else:
            # logger.warning(f'Unexpected peak amount on {button}: {count}, lines={lines}')
            # self.device.image_save()
            return False

    def is_combat_auto(self) -> bool:
        return self._is_combat_button_active(COMBAT_AUTO)

    def is_combat_speed_2x(self) -> bool:
        return self._is_combat_button_active(COMBAT_SPEED_2X)

    def combat_state_reset(self):
        self._combat_auto_checked = False
        self._combat_2x_checked = False

    def handle_combat_state(self, auto=True, speed_2x=True):
        """
        Set combat auto and 2X speed. Enable both by default.

        Returns:
            bool: If clicked
        """
        if self._combat_auto_checked and self._combat_2x_checked:
            return False
        if not self.is_combat_executing():
            return False

        if not self._combat_2x_checked:
            if speed_2x:
                if self.is_combat_speed_2x():
                    logger.info('_combat_2x_checked')
                    self._combat_2x_checked = True
                else:
                    if self._combat_click_interval.reached():
                        self.device.click(COMBAT_SPEED_2X)
                        self._combat_click_interval.reset()
                        return True
            else:
                if self.is_combat_speed_2x():
                    if self._combat_click_interval.reached():
                        self.device.click(COMBAT_SPEED_2X)
                        self._combat_click_interval.reset()
                        return True
                else:
                    logger.info('_combat_2x_checked')
                    self._combat_2x_checked = True

        if not self._combat_auto_checked:
            if auto:
                if self.is_combat_auto():
                    logger.info('_combat_auto_checked')
                    self._combat_auto_checked = True
                else:
                    if self._combat_click_interval.reached():
                        self.device.click(COMBAT_AUTO)
                        self._combat_click_interval.reset()
                        return True
            else:
                if self.is_combat_auto():
                    if self._combat_click_interval.reached():
                        self.device.click(COMBAT_AUTO)
                        self._combat_click_interval.reset()
                        return True
                else:
                    logger.info('_combat_auto_checked')
                    self._combat_auto_checked = True

        return False
