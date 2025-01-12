from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import *
from module.logger import logger
from module.os.assets import *
from module.os_handler.map_event import MapEventHandler


class FleetSelector:
    """
    Similar to FleetOperator.
    """
    FLEET_BAR_SHAPE_Y = 42
    FLEET_BAR_MARGIN_Y = 11
    FLEET_BAR_ACTIVE_STD = 45  # Active: 67, inactive: 12.

    def __init__(self, main):
        """
        Args:
            main (OSFleetSelector): Alas module
        """
        self._choose = FLEET_CHOOSE
        self._bar = FLEET_BAR
        self.main = main

    def get(self):
        """
        Returns:
            int: Index of current fleet, 1 to 4. return 0 if unrecognized.
        """
        for index, button in enumerate([FLEET_1, FLEET_2, FLEET_3, FLEET_4]):
            if self.main.appear(button, offset=(20, 20), similarity=0.75):
                return index + 1

        logger.info('Unknown OpSi fleet')
        return 0

    def bar_opened(self):
        # Check the 3-13 column
        area = self._bar.area
        area = (area[0] + 3, area[1], area[0] + 13, area[3])
        # Should have at least 2 gray option and 1 blue option.
        return self.main.image_color_count(area, color=(239, 243, 247), threshold=221, count=400) \
               and self.main.image_color_count(area, color=(66, 125, 231), threshold=221, count=150)

    def parse_fleet_bar(self, image):
        """
        Args:
            image (np.ndarray): Image of dropdown menu.

        Returns:
            list: List of int. Currently selected fleet ranges from 1 to 4.
        """
        width, height = image_size(image)
        result = []
        for index, y in enumerate(range(0, height, self.FLEET_BAR_SHAPE_Y + self.FLEET_BAR_MARGIN_Y)):
            area = (0, y, width, y + self.FLEET_BAR_SHAPE_Y)
            mean = get_color(image, area)
            if np.std(mean, ddof=1) > self.FLEET_BAR_ACTIVE_STD:
                result.append(4 - index)

        logger.info('Current selected: %s' % str(result))
        return result

    def selected(self):
        """
        Returns:
            list: List of int. Currently selected fleet ranges from 1 to 4.
        """
        data = self.parse_fleet_bar(self.main.image_crop(self._bar, copy=False))
        return data

    def get_button(self, index):
        """
        Convert fleet index to the Button object on dropdown menu.

        Args:
            index (int): Fleet index, 1-4.

        Returns:
            Button: Button instance.
        """
        index = 5 - index
        area = area_offset(area=(
            0,
            (self.FLEET_BAR_SHAPE_Y + self.FLEET_BAR_MARGIN_Y) * (index - 1),
            self._bar.area[2] - self._bar.area[0],
            (self.FLEET_BAR_SHAPE_Y + self.FLEET_BAR_MARGIN_Y) * (index - 1) + self.FLEET_BAR_SHAPE_Y
        ), offset=(self._bar.area[0:2]))
        area = area_pad(area, pad=3)
        index = 5 - index
        return Button(area=(), color=(), button=area, name='%s_INDEX_%s' % (str(self._bar), str(index)))

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

            if main.handle_map_event():
                click_timer.reset()
                continue

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

            if main.handle_map_event():
                click_timer.reset()
                continue

            if not self.bar_opened():
                # End
                if self.get() == index:
                    break
                # Game can't response that fast
                elif click_timer.reached():
                    self.open()

            # Click
            if click_timer.reached():
                main.device.click(button)
                click_timer.reset()

    def ensure_to_be(self, index, skip_first_screenshot=True):
        """
        Set to a specific fleet.

        Args:
            index (int): Fleet index, 1-4.
            skip_first_screenshot (bool):

        Returns:
            bool: If fleet switched.
        """
        confirm_timer = Timer(1.5, count=5).start()
        main = self.main
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            if confirm_timer.reached():
                break

            if main.handle_map_event():
                confirm_timer.reset()
                continue

            current = self.get()
            if current == index:
                logger.info(f'It is fleet {index} already')
                return False
            elif current > 0:
                logger.info(f'Ensure fleet to be {index}')
                self.open()
                self.click(index)
                return True

        logger.warning('Unknown OpSi fleet, use current fleet instead')
        return False


class OSFleetSelector(MapEventHandler):
    @cached_property
    def fleet_selector(self):
        return FleetSelector(main=self)
