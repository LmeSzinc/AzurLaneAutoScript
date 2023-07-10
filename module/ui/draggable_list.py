from typing import Optional

import numpy as np

from module.base.base import ModuleBase
from module.base.button import ButtonWrapper
from module.base.timer import Timer
from module.base.utils import area_size, random_rectangle_vector_opted
from module.logger import logger
from module.ocr.keyword import Keyword
from module.ocr.ocr import OcrResultButton


class DraggableList:
    """
    A wrapper to handle draggable lists like
    - Simulated Universe
    - Calyx (Golden)
    - Calyx (Crimson)
    - Stagnant Shadow
    - Cavern of Corrosion
    """
    drag_vector = (0.65, 0.85)

    def __init__(
            self,
            name,
            keyword_class,
            ocr_class,
            search_button: ButtonWrapper,
            check_row_order: bool = True,
            active_color: tuple[int, int, int] = (190, 175, 124),
            drag_direction: str = "down"
    ):
        """
        Args:
            name:
            keyword_class: Keyword
            search_button:
            drag_direction: Default drag direction to higher index
        """
        self.name = name
        self.keyword_class = keyword_class
        self.ocr_class = ocr_class
        if isinstance(keyword_class, list):
            keyword_class = keyword_class[0]
        self.known_rows = list(keyword_class.instances.values())
        self.search_button = search_button
        self.check_row_order = check_row_order
        self.active_color = active_color
        self.drag_direction = drag_direction

        self.row_min = 1
        self.row_max = len(self.known_rows)
        self.cur_min = 1
        self.cur_max = 1
        self.cur_buttons: list[OcrResultButton] = []

    def __str__(self):
        return f'DraggableList({self.name})'

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.name)

    def keyword2index(self, row: Keyword) -> int:
        try:
            return self.known_rows.index(row) + 1
        except ValueError:
            # logger.warning(f'Row "{row}" does not belong to {self}')
            return 0

    def keyword2button(self, row: Keyword, show_warning=True) -> Optional[OcrResultButton]:
        for button in self.cur_buttons:
            if button == row:
                return button

        if show_warning:
            logger.warning(f'Keyword {row} is not in current rows of {self}')
            logger.warning(f'Current rows: {self.cur_buttons}')
        return None

    def load_rows(self, main: ModuleBase):
        """
        Parse current rows to get list position.
        """
        self.cur_buttons = self.ocr_class(self.search_button) \
            .matched_ocr(main.device.image, self.keyword_class)
        # Get indexes
        indexes = [self.keyword2index(row.matched_keyword)
                   for row in self.cur_buttons]
        indexes = [index for index in indexes if index]
        # Check row order
        if self.check_row_order and len(indexes) >= 2:
            if not np.all(np.diff(indexes) > 0):
                logger.warning(
                    f'Rows given to {self} are not ascending sorted')
        if not indexes:
            logger.warning(f'No valid rows loaded into {self}')
            return

        self.cur_min = min(indexes)
        self.cur_max = max(indexes)
        logger.attr(self.name, f'{self.cur_min} - {self.cur_max}')

    def drag_page(self, direction: str, main: ModuleBase, vector=None):
        """
        Args:
            direction: up, down, left, right
            main:
            vector (tuple[float, float]): Specific `drag_vector`, None by default to use `self.drag_vector`
        """
        if vector is None:
            vector = self.drag_vector
        vector = np.random.uniform(*vector)
        width, height = area_size(self.search_button.button)
        if direction == 'up':
            vector = (0, vector * height)
        elif direction == 'down':
            vector = (0, -vector * height)
        elif direction == 'left':
            vector = (vector * width, 0)
        elif direction == 'right':
            vector = (-vector * width, 0)
        else:
            logger.warning(f'Unknown drag direction: {direction}')
            return

        p1, p2 = random_rectangle_vector_opted(vector, box=self.search_button.button)
        main.device.drag(p1, p2, name=f'{self.name}_DRAG')

    def reverse_direction(self, direction):
        if direction == 'up':
            return 'down'
        if direction == 'down':
            return 'up'
        if direction == 'left':
            return 'right'
        if direction == 'right':
            return 'left'

    def insight_row(self, row: Keyword, main: ModuleBase, skip_first_screenshot=True) -> bool:
        """
        Args:
            row:
            main:
            skip_first_screenshot:

        Returns:
            If success
        """
        row_index = self.keyword2index(row)
        if not row_index:
            logger.warning(f'Insight row {row} but index unknown')
            return False

        logger.info(f'Insight row: {row}, index={row_index}')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            self.load_rows(main=main)

            # End
            if self.cur_min <= row_index <= self.cur_max:
                break

            # Drag pages
            if row_index < self.cur_min:
                self.drag_page(self.reverse_direction(self.drag_direction), main=main)
            elif self.cur_max < row_index:
                self.drag_page(self.drag_direction, main=main)

            # Wait for bottoming out
            main.wait_until_stable(self.search_button, timer=Timer(
                0, count=0), timeout=Timer(1.5, count=5))
            skip_first_screenshot = True

        return True

    def is_row_selected(self, button: OcrResultButton, main: ModuleBase) -> bool:
        # Having gold letters
        if main.image_color_count(button, color=self.active_color, threshold=221, count=50):
            return True

        return False

    def get_selected_row(self, main: ModuleBase) -> Optional[OcrResultButton]:
        """
        `load_rows()` must be called before `get_selected_row()`.
        """
        for row in self.cur_buttons:
            if self.is_row_selected(row, main=main):
                return row
        return None

    def select_row(self, row: Keyword, main: ModuleBase, insight=True, skip_first_screenshot=True):
        """
        Args:
            row:
            main:
            insight: If call `insight_row()` before selecting
            skip_first_screenshot:

        Returns:
            If success
        """
        if insight:
            result = self.insight_row(
                row, main=main, skip_first_screenshot=skip_first_screenshot)
            if not result:
                return False

        logger.info(f'Select row: {row}')
        skip_first_screenshot = True
        interval = Timer(5)
        skip_first_load_rows = True
        load_rows_interval = Timer(1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            if skip_first_load_rows:
                skip_first_load_rows = False
                load_rows_interval.reset()
            else:
                if load_rows_interval.reached():
                    self.load_rows(main=main)
                    load_rows_interval.reset()

            button = self.keyword2button(row)
            if not button:
                return False

            # End
            if self.is_row_selected(button, main=main):
                logger.info(f'Row selected at {row}')
                return True

            # Click
            if interval.reached():
                main.device.click(button)
                interval.reset()
