from typing import Optional

import numpy as np

from module.base.base import ModuleBase
from module.base.button import ButtonWrapper
from module.base.timer import Timer
from module.base.utils import area_size
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

    def __init__(
            self,
            name,
            keyword_class,
            ocr_class,
            search_button: ButtonWrapper,
    ):
        """
        Args:
            name:
            keyword_class: Keyword
            search_button:
        """
        self.name = name
        self.keyword_class = keyword_class
        self.ocr_class = ocr_class
        self.known_rows = list(keyword_class.instances.values())
        self.search_button = search_button

        self.row_min = 1
        self.row_max = len(self.known_rows)
        self.cur_min = 1
        self.cur_max = 1
        self.cur_buttons: list[OcrResultButton] = []

        self.drag_vector = (0.65, 0.85)

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
            logger.warning(f'Row "{row}" does not belong to {self}')
            return 0

    def keyword2button(self, row: Keyword) -> Optional[OcrResultButton]:
        for button in self.cur_buttons:
            if button == row:
                return button

        logger.warning(f'Keyword {row} is not in current rows of {self}')
        logger.warning(f'Current rows: {self.cur_buttons}')
        return None

    def load_rows(self, main: ModuleBase):
        """
        Parse current rows to get list position.
        """
        self.cur_buttons = self.ocr_class(self.search_button) \
            .matched_ocr(main.device.image, keyword_class=self.keyword_class)
        # Get indexes
        indexes = [self.keyword2index(row.matched_keyword) for row in self.cur_buttons]
        indexes = [index for index in indexes if index]
        # Check row order
        if len(indexes) >= 2:
            if not np.all(np.diff(indexes) > 0):
                logger.warning(f'Rows given to {self} are not ascending sorted')
        if not indexes:
            logger.warning(f'No valid rows loaded into {self}')
            return

        self.cur_min = min(indexes)
        self.cur_max = max(indexes)
        logger.attr(self.name, f'{self.cur_min} - {self.cur_max}')

    def _page_drag(self, direction: str, main: ModuleBase):
        vector = np.random.uniform(*self.drag_vector)
        width, height = area_size(self.search_button.button)
        if direction == 'down':
            vector = (0, vector * height)
        elif direction == 'up':
            vector = (0, -vector * height)
        elif direction == 'left':
            vector = (-vector * width, 0)
        elif direction == 'right':
            vector = (vector * width, 0)
        else:
            logger.warning(f'Unknown drag direction: {direction}')
            return
        main.device.swipe_vector(
            vector, box=self.search_button.button, random_range=(-10, -10, 10, 10), name=f'{self.name}_DRAG')

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
                self._page_drag('down', main=main)
            elif self.cur_max < row_index:
                self._page_drag('up', main=main)
            # Wait for bottoming out
            main.wait_until_stable(self.search_button, timer=Timer(0, count=0), timeout=Timer(1.5, count=5))
            skip_first_screenshot = True

        return True

    def is_row_selected(self, row: Keyword, main: ModuleBase) -> bool:
        button = self.keyword2button(row)
        if not button:
            return False

        # Having gold letters
        if main.image_color_count(button, color=(190, 175, 124), threshold=221, count=50):
            return True

        return False

    def select_row(self, row: Keyword, main: ModuleBase, skip_first_screenshot=True):
        """
        Args:
            row:
            main:
            skip_first_screenshot:

        Returns:
            If success
        """
        result = self.insight_row(row, main=main, skip_first_screenshot=skip_first_screenshot)
        if not result:
            return False

        logger.info(f'Select row: {row}')
        skip_first_screenshot = True
        interval = Timer(5)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            # End
            if self.is_row_selected(row, main=main):
                logger.info('Row selected')
                break

            # Click
            if interval.reached():
                main.device.click(self.keyword2button(row))
                interval.reset()
