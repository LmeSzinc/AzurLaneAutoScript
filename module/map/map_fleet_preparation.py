import numpy as np
from scipy import signal

from module.base.button import Button
from module.base.timer import Timer
from module.base.utils import *
from module.exception import RequestHumanTakeover
from module.handler.assets import AUTO_SEARCH_SET_MOB, AUTO_SEARCH_SET_BOSS, \
    AUTO_SEARCH_SET_ALL, AUTO_SEARCH_SET_STANDBY, \
    AUTO_SEARCH_SET_SUB_AUTO, AUTO_SEARCH_SET_SUB_STANDBY
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.map.assets import *


class FleetOperator:
    FLEET_BAR_SHAPE_Y = 33
    FLEET_BAR_MARGIN_Y = 9
    FLEET_BAR_ACTIVE_STD = 45  # Active: 67, inactive: 12.
    FLEET_IN_USE_STD = 27  # In use 52, not in use (3, 6).

    OFFSET = (-20, -80, 20, 5)

    def __init__(self, choose, advice, bar, clear, in_use, hard_satisfied, main):
        """
        Args:
            choose (Button): Button to activate or deactivate dropdown menu.
            advice (Button): Button to recommend ships.
            bar (Button): Dropdown menu for fleet selection。
            clear (Button): Button to clear current fleet.
            in_use (Button): Button to detect if it's using current fleet.
            hard_satisfied (Button): Area to detect if fleet satiesfies hard restrictions.
            main (InfoHandler): Alas module.
        """
        self._choose = choose
        self._advice = advice
        self._bar = bar
        self._clear = clear
        self._in_use = in_use
        self._hard_satisfied = hard_satisfied
        self.main = main

        if main.appear(clear, offset=FleetOperator.OFFSET):
            choose.load_offset(clear)
            bar.load_offset(clear)
            in_use.load_offset(clear)
            hard_satisfied.load_offset(clear)

    def __str__(self):
        return str(self._choose)[:-7]

    def parse_fleet_bar(self, image):
        """
        Args:
            image (np.ndarray): Image of dropdown menu.

        Returns:
            list: List of int. Currently selected fleet ranges from 1 to 6.
        """
        width, height = image_size(image)
        result = []
        for index, y in enumerate(range(0, height, self.FLEET_BAR_SHAPE_Y + self.FLEET_BAR_MARGIN_Y)):
            area = (0, y, width, y + self.FLEET_BAR_SHAPE_Y)
            mean = get_color(image, area)
            if np.std(mean, ddof=1) > self.FLEET_BAR_ACTIVE_STD:
                result.append(index + 1)
        logger.info('Current selected: %s' % str(result))
        return result

    def get_button(self, index):
        """
        Convert fleet index to the Button object on dropdown menu.

        Args:
            index (int): Fleet index, 1-6.

        Returns:
            Button: Button instance.
        """
        bar = self._bar.button
        area = area_offset(area=(
            0,
            (self.FLEET_BAR_SHAPE_Y + self.FLEET_BAR_MARGIN_Y) * (index - 1),
            bar[2] - bar[0],
            (self.FLEET_BAR_SHAPE_Y + self.FLEET_BAR_MARGIN_Y) * (index - 1) + self.FLEET_BAR_SHAPE_Y
        ), offset=(bar[0:2]))
        return Button(area=(), color=(), button=area, name='%s_INDEX_%s' % (str(self._bar), str(index)))

    def allow(self):
        """
        Returns:
            bool: If current fleet is allow to be chosen.
        """
        return self.main.appear(self._clear, offset=FleetOperator.OFFSET)

    def is_hard(self):
        """
        Returns:
            bool: Whether to have a recommend. If so, this stage is a hard campaign.
        """
        return self.main.appear(self._advice, offset=FleetOperator.OFFSET)

    def is_hard_satisfied(self):
        """
        Detect how many light orange lines are there.
        Having lines means current map has stat limits and user has satisfied at least one of them,
        so this is a hard map.

        Returns:
            bool: If current fleet satisfies hard restrictions.
                Or None if this is not a hard mode
        """
        if not self.is_hard():
            return None

        area = self._hard_satisfied.button
        image = color_similarity_2d(self.main.image_crop(area, copy=False), color=(249, 199, 0))
        height = cv2.reduce(image, 1, cv2.REDUCE_AVG).flatten()
        parameters = {'height': 180, 'distance': 5}
        peaks, _ = signal.find_peaks(height, **parameters)
        lines = len(peaks)
        # logger.attr('Light_orange_line', lines)
        return lines > 0

    def raise_hard_not_satisfied(self):
        if self.is_hard_satisfied() is False:
            stage = self.main.config.Campaign_Name
            logger.critical(f'Stage "{stage}" is a hard mode, '
                            f'please prepare your fleet "{str(self)}" in game before running Alas')
            raise RequestHumanTakeover

    def clear(self, skip_first_screenshot=True):
        """
        Clear chosen fleet.
        """
        main = self.main
        click_timer = Timer(3, count=6)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            # Popups when clearing hard fleets
            if self.main.handle_popup_confirm(str(self._clear)):
                continue

            # End
            if not self.in_use():
                break

            # Click
            if click_timer.reached():
                main.device.click(self._clear)
                click_timer.reset()

    def recommend(self, skip_first_screenshot=True):
        """
        Recommend fleet
        """
        main = self.main
        click_timer = Timer(3, count=6)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            # End
            if self.in_use():
                break

            # Click
            if click_timer.reached():
                main.device.click(self._choose)
                click_timer.reset()

    def open(self, skip_first_screenshot=True):
        """
        Activate dropdown menu for fleet selection.
        """
        main = self.main
        click_timer = Timer(3, count=6)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            # End
            if self.bar_opened():
                break

            # Click
            if click_timer.reached():
                main.device.click(self._choose)
                click_timer.reset()

    def close(self, skip_first_screenshot=True):
        """
        Deactivate dropdown menu for fleet selection.
        """
        main = self.main
        click_timer = Timer(3, count=6)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            # End
            if not self.bar_opened():
                break

            # Click
            if click_timer.reached():
                main.device.click(self._choose)
                click_timer.reset()

    def click(self, index, skip_first_screenshot=True):
        """
        Choose a fleet on dropdown menu, and dropdown deactivated.

        Args:
            index (int): Fleet index, 1-6.
            skip_first_screenshot (bool):
        """
        main = self.main
        button = self.get_button(index)
        click_timer = Timer(3, count=6)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            if not self.bar_opened():
                # End
                if self.in_use():
                    break
                else:
                    self.open()

            # Click
            if click_timer.reached():
                main.device.click(button)
                click_timer.reset()

    def selected(self):
        """
        Returns:
            list: List of int. Currently selected fleet ranges from 1 to 6.
        """
        data = self.parse_fleet_bar(self.main.image_crop(self._bar.button, copy=False))
        return data

    def in_use(self):
        """
        Returns:
            bool: If has selected to any fleet.
        """
        # Handle the info bar of auto search info.
        # if area_cross_area(self._in_use.area, INFO_BAR_1.area):
        #     self.main.handle_info_bar()

        # Cropping FLEET_*_IN_USE to avoid detecting info_bar, also do the trick.
        # It also avoids wasting time on handling the info_bar.
        image = rgb2gray(self.main.image_crop(self._in_use.button, copy=False))
        return np.std(image.flatten(), ddof=1) > self.FLEET_IN_USE_STD

    def bar_opened(self):
        """
        Returns:
            bool: If dropdown menu appears.
        """
        # Check the brightness of the rightest column of the bar area.
        luma = rgb2gray(self.main.image_crop(self._bar.button, copy=False))[:, -1]
        # FLEET_PREPARATION is about 146~155
        return np.sum(luma > 168) / luma.size > 0.5

    def ensure_to_be(self, index):
        """
        Set to a specific fleet.

        Args:
            index (int): Fleet index, 1-6.
        """
        self.open()
        if index in self.selected():
            self.close()
        else:
            self.click(index)


class FleetPreparation(InfoHandler):
    map_fleet_checked = False
    map_is_hard_mode = False

    def fleet_preparation(self):
        """Change fleets.

        Returns:
            bool: True if changed.
        """
        logger.info(f'Using fleet: {[self.config.Fleet_Fleet1, self.config.Fleet_Fleet2, self.config.Submarine_Fleet]}')
        if self.map_fleet_checked:
            return False

        fleet_1 = FleetOperator(
            choose=FLEET_1_CHOOSE, advice=FLEET_1_ADVICE, bar=FLEET_1_BAR, clear=FLEET_1_CLEAR,
            in_use=FLEET_1_IN_USE, hard_satisfied=FLEET_1_HARD_SATIESFIED, main=self)
        fleet_2 = FleetOperator(
            choose=FLEET_2_CHOOSE, advice=FLEET_2_ADVICE, bar=FLEET_2_BAR, clear=FLEET_2_CLEAR,
            in_use=FLEET_2_IN_USE, hard_satisfied=FLEET_2_HARD_SATIESFIED, main=self)
        submarine = FleetOperator(
            choose=SUBMARINE_CHOOSE, advice=SUBMARINE_ADVICE, bar=SUBMARINE_BAR, clear=SUBMARINE_CLEAR,
            in_use=SUBMARINE_IN_USE, hard_satisfied=SUBMARINE_HARD_SATIESFIED, main=self)

        # Check if ship is prepared in hard mode
        h1, h2, h3 = fleet_1.is_hard_satisfied(), fleet_2.is_hard_satisfied(), submarine.is_hard_satisfied()
        logger.info(f'Hard satisfied: Fleet_1: {h1}, Fleet_2: {h2}, Submarine: {h3}')
        if self.config.SERVER in ['cn', 'en', 'jp']:
            if self.config.Fleet_Fleet1:
                fleet_1.raise_hard_not_satisfied()
            if self.config.Fleet_Fleet2:
                fleet_2.raise_hard_not_satisfied()
            if self.config.Submarine_Fleet:
                submarine.raise_hard_not_satisfied()

        # Skip fleet preparation in hard mode
        self.map_is_hard_mode = h1 or h2 or h3
        if self.map_is_hard_mode:
            logger.info('Hard Campaign. No fleet preparation')
            # Clear submarine if user did not set a submarine fleet
            if submarine.allow():
                if self.config.Submarine_Fleet:
                    pass
                else:
                    submarine.clear()
            return False

        # Submarine.
        if submarine.allow():
            if self.config.Submarine_Fleet:
                submarine.ensure_to_be(self.config.Submarine_Fleet)
            else:
                submarine.clear()

        # No need, this may clear FLEET_2 by mistake, clear FLEET_2 in map config.
        # if not fleet_2.allow():
        #     self.config.FLEET_2 = 0

        if self.config.Fleet_Fleet2:
            # Using both fleets.
            # Force to set it again.
            # Fleets may reversed, because AL no longer treat the fleet with smaller index as first fleet
            fleet_2.clear()
            fleet_1.ensure_to_be(self.config.Fleet_Fleet1)
            fleet_2.ensure_to_be(self.config.Fleet_Fleet2)
        else:
            # Not using fleet 2.
            if fleet_2.allow():
                fleet_2.clear()
            fleet_1.ensure_to_be(self.config.Fleet_Fleet1)

        # Check if submarine is empty again.
        if submarine.allow():
            logger.attr('map_allow_submarine', True)
            if self.config.Submarine_Fleet:
                pass
            else:
                submarine.clear()
        else:
            logger.attr('map_allow_submarine', False)
            self.config.SUBMARINE = 0

        if self.appear(FLEET_1_CLEAR, offset=(-20, -80, 20, 5)):
            AUTO_SEARCH_SET_MOB.load_offset(FLEET_1_CLEAR)
            AUTO_SEARCH_SET_BOSS.load_offset(FLEET_1_CLEAR)
            AUTO_SEARCH_SET_ALL.load_offset(FLEET_1_CLEAR)
            AUTO_SEARCH_SET_STANDBY.load_offset(FLEET_1_CLEAR)
        if self.appear(SUBMARINE_CLEAR, offset=(-20, -80, 20, 5)):
            AUTO_SEARCH_SET_SUB_AUTO.load_offset(SUBMARINE_CLEAR)
            AUTO_SEARCH_SET_SUB_STANDBY.load_offset(SUBMARINE_CLEAR)

        return True
