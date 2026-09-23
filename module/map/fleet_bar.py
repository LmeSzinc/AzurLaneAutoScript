import cv2

from module.base.base import ModuleBase
from module.base.decorator import cached_property
from module.base.utils import area_cross_area, area_in_area, color_mask, crop, point_in_area
from module.logger import logger
from module.map.assets import FLEET_PREPARATION


class FleetOption:
    def __init__(self, area):
        self.area = area
        self.color = (0, 0, 0)
        self.button = area
        self.index = 0
        self.selected = False

    def __repr__(self):
        return f'{self.__class__.__name__}(area={self.area}, index={self.index}, selected={self.selected})'

    def __str__(self):
        return f'{self.__class__.__name__}_{self.index}'

    def pretty(self):
        if self.selected:
            return f'[{self.index}]'
        else:
            return f' {self.index} '


class FleetBarDetector:
    def __init__(self, main, bar, choose=None):
        """
        Args:
            main (ModuleBase):
            bar (Button):
            choose (Button): Optional choose button to check if first option is below recommend
        """
        self.area = bar.button
        self.main = main
        self.image = main.device.image
        self.choose = choose

        self.option_shape = (169, 33)
        # option might be covered by info_bar, half width to full width is allowed
        self.shape_range = (88, 33 - 5, 169 + 5, 55 + 5)

    def _find_option(self, image):
        """
        Find option button from image mask

        Returns:
            list[FleetOptionButton]:
        """
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        buttons = []
        for contour in contours:
            # x, y, w, h
            x, y, w, h = cv2.boundingRect(contour)
            if not point_in_area((w, h), self.shape_range, threshold=0):
                continue
            x += self.area[0]
            y += self.area[1]
            area = (x, y, x + w, y + h)
            if self.avoid_area is not None:
                if area_in_area(self.avoid_area, area, threshold=0):
                    continue
                if area_in_area(area, self.avoid_area, threshold=0):
                    continue
                if area_cross_area(self.avoid_area, area, threshold=0):
                    continue

            buttons.append(FleetOption(area))

        return buttons

    @cached_property
    def avoid_area(self):
        # delete options from FLEET_PREPARATION
        if self.main.appear(FLEET_PREPARATION, offset=(20, 50)):
            return FLEET_PREPARATION.button
        return None

    @cached_property
    def options(self):
        """
        Returns:
            dict[int, FleetOption]:
        """
        image = crop(self.image, self.area, copy=False)
        # selected option in gradient orange
        orange = color_mask(image, (220, 161, 90), threshold=50)
        orange2 = color_mask(image, (248, 209, 70), threshold=50)
        cv2.bitwise_or(orange, orange2, dst=orange)
        # white letter on orange background
        orange2 = color_mask(image, (251, 231, 157), threshold=30)
        cv2.bitwise_or(orange, orange2, dst=orange)
        selected = self._find_option(orange)

        # non-selected option in gradient light-gray
        gray = color_mask(image, (220, 207, 232), threshold=30)
        gray2 = color_mask(image, (166, 175, 199), threshold=30)
        cv2.bitwise_or(gray, gray2, dst=gray)
        # white letter on light-gray background
        gray2 = color_mask(image, (203, 208, 222), threshold=30)
        cv2.bitwise_or(gray, gray2, dst=gray)
        non_selected = self._find_option(gray)

        # re-index
        for button in selected:
            button.selected = True
        options = sorted(selected + non_selected, key=lambda x: x.area[1])
        for index, button in enumerate(options, start=1):
            button.index = index

        logger.info('FleetOption: ' + ''.join([button.pretty() for button in options]))
        # validate
        amount = len(options)
        if amount == 1:
            logger.warning(f'FleetOption amount == 1, options={options}')
        elif amount > 6:
            logger.warning(f'FleetOption amount > 6, options={options}')
        elif 2 <= amount <= 6:
            # check option gaps
            prev_h = 0
            for button in options:
                if prev_h:
                    # options should just next to each other with little gaps
                    gap = button.area[1] - prev_h
                    if gap < self.option_shape[1]:
                        logger.warning(f'FleetOption gap too small on index={button.index}, options={options}')
                    if gap > self.option_shape[1] * 2:
                        logger.warning(f'FleetOption gap too large on index={button.index}, options={options}')
                else:
                    # first option should just below recommend button
                    if not self.choose:
                        continue
                    gap = button.area[1] - self.choose.button[3]
                    if gap < 0:
                        logger.warning(f'FleetOption first option is on the top of choose button, options={options}')
                    if gap > self.option_shape[1]:
                        logger.warning(f'FleetOption gap too large on first button, options={options}')

                prev_h = button.area[1]
        else:
            # no logs on empty options
            pass
        options = {button.index: button for button in options}
        return options
