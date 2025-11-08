from functools import reduce
from typing import List, Optional, Tuple

import cv2
import numpy as np

from module.base.utils import area_offset, color_similarity_2d, image_size, rgb2gray, xywh2xyxy
from module.event_hospital.assets import *
from module.event_hospital.ui import HospitalUI
from module.logger import logger
from module.raid.assets import RAID_FLEET_PREPARATION
from module.ui.page import page_hospital
from module.ui.scroll import Scroll


def merge_two_rects(
        r1: Tuple[int, int, int, int],
        r2: Tuple[int, int, int, int]
) -> Tuple[int, int, int, int]:
    return (
        min(r1[0], r2[0]),  # left
        min(r1[1], r2[1]),  # top
        max(r1[2], r2[2]),  # right
        max(r1[3], r2[3])  # bottom
    )


def merge_rows(list_word, merge):
    # Sort
    list_word = sorted(list_word, key=lambda x: x[1])

    # Merge words
    list_row = []
    current_row = []
    current_center = None
    for rect, center_y in list_word:
        if not current_row:
            current_row.append(rect)
            current_center = center_y
        elif abs(center_y - current_center) <= merge:
            current_row.append(rect)
        else:
            list_row.append(reduce(merge_two_rects, current_row))
            current_row = [rect]
            current_center = center_y

    if current_row:
        list_row.append(reduce(merge_two_rects, current_row))

    return list_row


class HospitalClue(HospitalUI):
    def get_clue_list(self) -> List[Button]:
        """
        Get list of aside buttons
        """
        area = CLUE_LIST.area
        image = self.image_crop(area, copy=False)

        # Mask for gray letters
        gray = color_similarity_2d(image, color=(132, 134, 148))
        cv2.inRange(gray, 215, 255, dst=gray)
        # Mask for selected aside (white letters)
        white = color_similarity_2d(image, color=(255, 255, 255))
        cv2.inRange(white, 215, 255, dst=white)
        # Clear gray mask around white pixels
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (200, 20))
        white_expanded = cv2.dilate(white, kernel)
        cv2.subtract(gray, white_expanded, dst=gray)
        # Mix
        cv2.bitwise_or(gray, white, dst=gray)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cv2.dilate(gray, kernel, dst=gray)

        # import matplotlib.pyplot as plt
        # plt.imshow(gray)
        # plt.show()
        # from PIL import Image
        # Image.fromarray(gray, mode='L').show()

        # Find rectangles
        list_word = []
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cont in contours:
            rect = cv2.boundingRect(cv2.convexHull(cont).astype(np.float32))
            # Filter with rectangle height, usually to be 16
            rect = xywh2xyxy(rect)
            # Check max_height
            if rect[3] - rect[1] < 12:
                # logger.warning(f'Text row too high: {rect}')
                continue
            center_y = (rect[1] + rect[3]) // 2
            list_word.append((rect, center_y))

        list_row = merge_rows(list_word, merge=5)
        list_row = [area_offset(r, offset=area[:2]) for r in list_row]
        list_button = [
            Button(area=rect, color=(), button=rect, name=f'CLUE_LIST_{i}')
            for i, rect in enumerate(list_row)
        ]
        return list_button

    def get_invest_button(self) -> Optional[Button]:
        """
        Get unfinished INVEST button from current image
        """
        area = INVEST_SEARCH.area
        image = self.image_crop(area, copy=False)
        image = rgb2gray(image)

        # Search INVEST
        buttons = TEMPLATE_INVEST.match_multi(image)
        buttons += TEMPLATE_INVEST2.match_multi(image)
        buttons = sorted(buttons, key=lambda b: b.area[1])
        count = len(buttons)
        if count == 0:
            return None
        buttons = [b.move(area[:2]) for b in buttons]
        if count == 1:
            # 1 INVEST button, Search bellow INVEST
            button = buttons[0]
            search = (area[0], button.button[3], area[2], area[3])
        else:
            # More than 1 INVEST, search middle
            button = buttons[0]
            second = buttons[1]
            search = (area[0], button.button[3], area[2], second.button[1])
        image = self.image_crop(search, copy=False)
        image = rgb2gray(image)

        # Check image size
        x, y = image_size(image)
        if y < 50:
            return None

        # Check if there's TEMPLATE_REMAIN_CURRENT TEMPLATE_REMAIN_TIMES bellow INVEST
        if TEMPLATE_REMAIN_CURRENT.match(image):
            return button
        if TEMPLATE_REMAIN_TIMES.match(image):
            return button
        return None

    def clue_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: Any sub page of hospital event
            out: is_in_clue
        """
        logger.info('Hospital clue enter')
        self.interval_clear(page_hospital.check_button)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.is_in_clue():
                break
            if self.handle_clue_exit():
                continue

    def clue_exit(self, skip_first_screenshot=True):
        """
        Pages:
            in: Any sub page of hospital event
            out: page_hospital
        """
        logger.info('Hospital clue exit')
        self.interval_clear(HOSIPITAL_CLUE_CHECK)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.ui_page_appear(page_hospital):
                break
            if self.handle_clue_exit():
                continue
            if self.appear_then_click(HOSIPITAL_CLUE_CHECK, offset=(20, 20), interval=2):
                continue

    def invest_enter(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            bool: If success to enter

        Pages:
            in: is_in_clue
            out: FLEET_PREPARATION
        """
        logger.info('Clue invest')
        self.interval_clear(HOSIPITAL_CLUE_CHECK)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear(RAID_FLEET_PREPARATION, offset=(30, 30)):
                return True

            if self.is_in_clue(interval=2):
                invest = next(self.iter_invest(), None)
                if invest is None:
                    logger.info('No more invest')
                    return False
                logger.info(f'is_in_clue -> {invest}')
                self.device.click(invest)
                self.interval_reset(HOSIPITAL_CLUE_CHECK, interval=2)
                continue
            if self.appear_then_click(HOSPITAL_BATTLE_PREPARE, offset=(20, 20), interval=2):
                continue
            if self.handle_get_clue():
                continue

    def iter_invest(self):
        """
        Yields:
            Button:
        """
        logger.hr('Iter invest')
        scroll = Scroll(INVEST_SCROLL, color=(107, 97, 107), name='INVEST_SCROLL')
        # No scroll, yield one button only
        if not scroll.appear(main=self):
            logger.info('No scroll')
            button = self.get_invest_button()
            if button:
                yield button
            return

        # Check current page
        button = self.get_invest_button()
        if button:
            yield button

        # Check top
        if not scroll.at_top(main=self):
            scroll.set_top(main=self)
            button = self.get_invest_button()
            if button:
                yield button
        # Iter page
        while 1:
            if scroll.at_bottom(main=self):
                logger.info(f'{scroll.name} reached end')
                return
            scroll.next_page(main=self, page=0.5)
            button = self.get_invest_button()
            if button:
                yield button

    def is_aside_selected(self, button: Button) -> bool:
        area = button.area
        search = CLUE_LIST.area
        # Search around if having dark background
        area = (search[0], area[1], search[2], area[3])
        return self.image_color_count(area, color=(82, 85, 107), threshold=221, count=500)

    def is_aside_checked(self, button: Button) -> bool:
        area = button.area
        search = CLUE_LIST.area
        # Search if there's any cyan
        # JP has text overflowed, set right to 308
        area = (search[0], area[1], 308, area[3])
        return self.image_color_count(area, color=(74, 130, 148), threshold=221, count=20)

    def iter_aside(self):
        """
        Yields:
            Button:
        """
        list_button = self.get_clue_list()
        for button in list_button:
            if self.is_aside_checked(button):
                continue
            yield button

    def select_aside(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            bool: True if success to select any unfinished aside
                False if all aside finished

        Pages:
            in: is_in_clue
        """
        logger.info(f'Select aside')
        aside = None
        self.interval_clear(HOSIPITAL_CLUE_CHECK)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if aside is not None and self.is_aside_selected(aside):
                return True
            if self.is_in_clue(interval=2):
                aside = next(self.iter_aside(), None)
                if aside is None:
                    logger.info('No more aside')
                    return False
                logger.info(f'is_in_clue -> {aside}')
                self.device.click(aside)
                self.interval_reset(HOSIPITAL_CLUE_CHECK, interval=2)
                continue
            if self.handle_clue_exit():
                continue
