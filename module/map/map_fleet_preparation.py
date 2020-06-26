import numpy as np
from PIL import ImageStat

from module.base.base import ModuleBase
from module.base.button import Button
from module.base.utils import area_offset
from module.logger import logger
from module.map.assets import *


class FleetOperator:
    FLEET_BAR_SHAPE_Y = 36
    FLEET_BAR_MARGIN_Y = 6
    FLEET_BAR_ACTIVE_STD = 45  # Active: 67, inactive: 12.
    FLEET_IN_USE_STD = 20  # In use 52, not in use (3, 6).
    FLEET_PREPARE_OPERATION_SLEEP = (0.25, 0.35)

    def __init__(self, choose, bar, clear, in_use, main):
        """
        Args:
            choose(Button):
            bar(Button):
            clear(Button):
        """
        self._choose = choose
        self._bar = bar
        self._clear = clear
        self._in_use = in_use
        self.main = main

    def __str__(self):
        return str(self._choose)[:-7]

    def parse_fleet_bar(self, image):
        """
        Args:
            image(PIL.Image.Image): Image of fleet choosing bar.

        Returns:
            list: List of int. Chosen fleet range from 1 to 6.
        """
        result = []
        for index, y in enumerate(range(0, image.size[1], self.FLEET_BAR_SHAPE_Y + self.FLEET_BAR_MARGIN_Y)):
            area = (0, y, image.size[0], y + self.FLEET_BAR_SHAPE_Y)
            stat = ImageStat.Stat(image.crop(area))
            if np.std(stat.mean, ddof=1) > self.FLEET_BAR_ACTIVE_STD:
                result.append(index + 1)
        logger.info('Current selected: %s' % str(result))
        return result

    def get_button(self, index):
        """
        Args:
            index(int): Fleet index, 1-6.

        Returns:
            Button: Button instance.
        """
        area = area_offset(area=(
            0,
            (self.FLEET_BAR_SHAPE_Y + self.FLEET_BAR_MARGIN_Y) * (index - 1),
            self._bar.area[2] - self._bar.area[0],
            (self.FLEET_BAR_SHAPE_Y + self.FLEET_BAR_MARGIN_Y) * (index - 1) + self.FLEET_BAR_SHAPE_Y
        ), offset=(self._bar.area[0:2]))
        return Button(area=(), color=(), button=area, name='%s_INDEX_%s' % (str(self._bar), str(index)))

    def allow(self):
        return self.main.appear(self._choose)

    def clear(self):
        self.main.device.click(self._clear)
        self.main.device.sleep(self.FLEET_PREPARE_OPERATION_SLEEP)

    def open(self):
        self.main.device.click(self._choose)
        self.main.device.sleep(self.FLEET_PREPARE_OPERATION_SLEEP)
        self.main.device.screenshot()

    def close(self):
        self.main.device.click(self._choose)
        self.main.device.sleep(self.FLEET_PREPARE_OPERATION_SLEEP)
        self.main.device.screenshot()

    def click(self, index):
        self.main.device.click(self.get_button(index))
        self.main.device.sleep(self.FLEET_PREPARE_OPERATION_SLEEP)
        self.main.device.screenshot()

    def selected(self):
        data = self.parse_fleet_bar(self.main.device.image.crop(self._bar.area))
        return data

    def in_use(self):
        image = np.array(self.main.device.image.crop(self._in_use.area).convert('L'))
        return np.std(image.flatten(), ddof=1) > self.FLEET_IN_USE_STD

    def ensure_to_be(self, index):
        self.open()
        if index in self.selected():
            self.close()
        else:
            self.click(index)


class FleetPreparation(ModuleBase):
    map_fleet_checked = False

    def fleet_preparation(self):
        """Change fleets.

        Returns:
            bool: True if changed.
        """
        logger.info(f'Using fleet: {[self.config.FLEET_1, self.config.FLEET_2, self.config.SUBMARINE]}')
        if self.map_fleet_checked:
            return False
        if self.appear(FLEET_PREPARATION_HARD_1) or self.appear(FLEET_PREPARATION_HARD_2):
            logger.info('Hard Campaign. No fleet preparation')
            return False

        fleet_1 = FleetOperator(
            choose=FLEET_1_CHOOSE, bar=FLEET_1_BAR, clear=FLEET_1_CLEAR, in_use=FLEET_1_IN_USE, main=self)
        fleet_2 = FleetOperator(
            choose=FLEET_2_CHOOSE, bar=FLEET_2_BAR, clear=FLEET_2_CLEAR, in_use=FLEET_2_IN_USE, main=self)
        submarine = FleetOperator(
            choose=SUBMARINE_CHOOSE, bar=SUBMARINE_BAR, clear=SUBMARINE_CLEAR, in_use=SUBMARINE_IN_USE, main=self)

        # Submarine.
        if submarine.allow():
            if self.config.SUBMARINE:
                submarine.ensure_to_be(self.config.SUBMARINE)
            else:
                if submarine.in_use():
                    submarine.clear()

        # No need, this may clear FLEET_2 by mistake, clear FLEET_2 in map config.
        # if not fleet_2.allow():
        #     self.config.FLEET_2 = 0

        # Not using fleet 2.
        if not self.config.FLEET_2:
            if fleet_2.allow():
                if fleet_2.in_use():
                    fleet_2.clear()
            fleet_1.ensure_to_be(self.config.FLEET_1)
            self.map_fleet_checked = True
            return True

        # Using both fleets.
        fleet_1.open()
        selected = fleet_1.selected()
        if self.config.FLEET_1 in selected and self.config.FLEET_2 in selected:
            fleet_1.close()
            self.map_fleet_checked = True
            return True
        else:
            fleet_1.close()
            if fleet_2.in_use():
                fleet_2.clear()
            fleet_1.ensure_to_be(self.config.FLEET_1)
            fleet_2.ensure_to_be(self.config.FLEET_2)
            self.map_fleet_checked = True
            return True
