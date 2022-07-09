import numpy as np

from module.base.base import ModuleBase
from module.base.button import Button
from module.base.timer import Timer
from module.base.utils import color_similarity_2d, random_rectangle_point
from module.logger import logger


class Scroll:
    color_threshold = 221
    drag_threshold = 0.05
    edge_add = (0.1, 0.2)

    def __init__(self, area, color, is_vertical=True, name='Scroll'):
        """
        Args:
            area (Button, tuple): A button or area of the whole scroll.
            color (tuple): RGB of the scroll
            is_vertical (bool): True if vertical, false if horizontal.
            name (str):
        """
        if isinstance(area, Button):
            name = area.name
            area = area.area
        self.area = area
        self.color = color
        self.is_vertical = is_vertical
        self.name = name

        if self.is_vertical:
            self.total = self.area[3] - self.area[1]
        else:
            self.total = self.area[2] - self.area[0]
        # Just default value, will change in match_color()
        self.length = self.total / 2
        self.drag_interval = Timer(1)

    def match_color(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            np.ndarray: Shape (n,), dtype bool.
        """
        image = main.image_crop(self.area)
        image = color_similarity_2d(image, color=self.color)
        mask = np.max(image, axis=1 if self.is_vertical else 0) > self.color_threshold
        self.length = np.sum(mask)
        return mask

    def cal_position(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            float: 0 to 1.
        """
        mask = self.match_color(main)
        middle = np.mean(np.where(mask)[0])

        position = (middle - self.length / 2) / (self.total - self.length)
        position = position if position > 0 else 0.0
        position = position if position < 1 else 1.0
        logger.attr(self.name, f'{position:.2f} ({middle}-{self.length / 2})/({self.total}-{self.length})')
        return position

    def position_to_screen(self, position, random_range=(-0.05, 0.05)):
        """
        Convert scroll position to screen coordinates.
        Call cal_position() or match_color() to get length, before calling this.

        Args:
            position (int, float):
            random_range (tuple):

        Returns:
            tuple[int]: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y)
        """
        position = np.add(position, random_range)
        middle = position * (self.total - self.length) + self.length / 2
        middle = middle.astype(int)
        if self.is_vertical:
            middle += self.area[1]
            area = (self.area[0], middle[0], self.area[2], middle[1])
        else:
            middle += self.area[0]
            area = (middle[0], self.area[1], middle[1], self.area[3])
        return area

    def appear(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            bool
        """
        return np.mean(self.match_color(main)) > 0.1

    def at_top(self, main):
        return self.cal_position(main) < 0.05

    def at_bottom(self, main):
        return self.cal_position(main) > 0.95

    def set(self, position, main, random_range=(-0.05, 0.05), distance_check=True, skip_first_screenshot=True):
        """
        Set scroll to a specific position.

        Args:
            position (float, int): 0 to 1.
            main (ModuleBase):
            random_range (tuple(int, float)):
            distance_check (bool): Whether to drop short swipes
            skip_first_screenshot:
        """
        logger.info(f'{self.name} set to {position}')
        self.drag_interval.clear()
        if position == 0:
            random_range = np.subtract(0, self.edge_add)
        if position == 1:
            random_range = self.edge_add

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            current = self.cal_position(main)
            if abs(position - current) < self.drag_threshold:
                break
            if not self.length:
                logger.warning('Scroll disappeared, assume scroll set')
                break

            if self.drag_interval.reached():
                p1 = random_rectangle_point(self.position_to_screen(current), n=1)
                p2 = random_rectangle_point(self.position_to_screen(position, random_range=random_range), n=1)
                main.device.swipe(p1, p2, name=self.name, distance_check=distance_check)
                main.device.sleep(0.3)
                self.drag_interval.reset()

    def set_top(self, main, random_range=(-0.05, 0.05), skip_first_screenshot=True):
        return self.set(0.00, main=main, random_range=random_range, skip_first_screenshot=skip_first_screenshot)

    def set_bottom(self, main, random_range=(-0.05, 0.05), skip_first_screenshot=True):
        return self.set(1.00, main=main, random_range=random_range, skip_first_screenshot=skip_first_screenshot)

    def drag_page(self, page, main, random_range=(-0.05, 0.05), skip_first_screenshot=True):
        """
        Drag scroll forward or backward.

        Args:
            page (int, float): Relative position to drag. 1.0 means next page, -1.0 means previous page.
            main (ModuleBase):
            random_range (tuple[int]):
            skip_first_screenshot:
        """
        if not skip_first_screenshot:
            main.device.screenshot()
        current = self.cal_position(main)

        multiply = self.length / (self.total - self.length)
        target = current + page * multiply
        target = round(min(max(target, 0), 1), 3)
        self.set(target, main=main, random_range=random_range, skip_first_screenshot=True)

    def next_page(self, main, page=0.8, random_range=(-0.01, 0.01), skip_first_screenshot=True):
        self.drag_page(page, main=main, random_range=random_range, skip_first_screenshot=skip_first_screenshot)

    def prev_page(self, main, page=0.8, random_range=(-0.01, 0.01), skip_first_screenshot=True):
        self.drag_page(-page, main=main, random_range=random_range, skip_first_screenshot=skip_first_screenshot)
