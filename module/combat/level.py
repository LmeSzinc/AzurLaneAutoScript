from module.base.base import ModuleBase
from module.base.button import *
from module.base.decorator import Config
from module.base.utils import get_color
from module.logger import logger
from module.ocr.ocr import Ocr

LV_GRID = ButtonGrid(origin=(58, 117), delta=(0, 100), button_shape=(48, 22), grid_shape=(1, 6))
# Part of char 'P' in front of the HP bars. Determine ship status by them.
# (255, 255, 255) for healthy ships, (107, 105, 107) for ships need repair, and others for blank space.
STATUS_GRID = ButtonGrid(origin=(29, 192), delta=(0, 100), button_shape=(2, 7), grid_shape=(1, 6))
COLOR_WHITE = (255, 255, 255)
COLOR_MASKED = (107, 105, 107)


class Level(ModuleBase):
    _lv = []
    _lv_before_battle=[]
    _has_ship = []
    _low_hp = []

    @property
    def lv(self):
        """
        Returns:
            list[str]:
        """
        return self._lv

    @lv.setter
    def lv(self, value):
        """
        Args:
            value (list[str]):
        """
        self._lv = value

    @property
    def lv_before_battle(self):
        """
        Returns:
            list[str]:
        """
        return self._lv_before_battle

    @lv_before_battle.setter
    def lv_before_battle(self, value):
        """
        Args:
            value (list[str]):
        """
        self._lv_before_battle = value

    @property
    def has_ship(self):
        """
        Returns:
            list[bool]:
        """
        return self._has_ship

    @has_ship.setter
    def has_ship(self, value):
        """
        Args:
            value (list[bool]):
        """
        self._has_ship = value

    @property
    def low_hp(self):
        """
        Returns:
            list[bool]:
        """
        return self._low_hp

    @low_hp.setter
    def low_hp(self, value):
        """
        Args:
            value (list[bool]):
        """
        self._low_hp = value
        
    def lv_reset(self):
        """
        Call this method after enter map.
        """
        self._lv = ['-1'] * 6
        self._lv_before_battle = ['-1'] * 6
        self._has_ship = [False] * 6
        self._low_hp = [False] * 6

    def lv_get(self, after_battle=False):
        """
        Args:
            after_battle (bool): True if called after battle else False.
        """
        self.lv_before_battle = self.lv if after_battle else ['-1'] * 6

        colors = [tuple(get_color(self.device.image, button.area).astype(int)) for button in STATUS_GRID.buttons()]
        self.has_ship = [color == COLOR_WHITE or color == COLOR_MASKED for color in colors]
        self.low_hp = [color == COLOR_MASKED for color in colors]
        self._lv_ocr()
        logger.attr('LEVEL', ',  '.join(data for data in self.lv))
        if after_battle:
            self.lv120_triggered()
        return self.lv

    def _lv_ocr(self):
        image = self.device.image
        # The mask on low hp ships turns COLOR_WHITE=(255, 255, 255) to COLOR_MASKED=(107, 105, 107),
        # so multiply all channels by a scalar can turn them back.
        scalar = np.mean(COLOR_WHITE) / np.mean(COLOR_MASKED)
        image_low_hp = Image.fromarray(cv2.addWeighted(np.array(image), scalar, np.array(image), 0, 0), 'RGB')
        lv = []
        for i in range(6):
            if not self.has_ship[i]:
                lv.append('-1')
                continue
            # The default argument 'threshold=128' makes some digits too thin to be recognized.
            ocr = Ocr(LV_GRID.buttons()[i], threshold=191, alphabet='0123456789LV')
            if self.low_hp[i]:
                level = ocr.ocr(image_low_hp)
            else:
                level = ocr.ocr(image)
            # strip 'LV'
            level = level[level.find('V') + 1:]
            lv.append(level)
        self.lv = lv

    def lv120_triggered(self):
        if not self.config.STOP_IF_REACH_LV120:
            return False
        for i in range(6):
            if self.lv[i] == '120' and self.lv_before_battle[i] == '119':
                logger.info(f'Position {i} LV.120 Reached')
                self.config.LV120_TRIGGERED = True
                return True
        return False
