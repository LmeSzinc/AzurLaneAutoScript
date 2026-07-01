import cv2
import numpy as np
from typing import List

from module.base.base import ModuleBase
from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import area_offset, color_similarity_2d, rgb2luma
from module.combat.assets import GET_ITEMS_1
from module.island.assets import *
from module.logger import logger
from module.ui.navbar import Navbar
from module.ui.ui import UI
from module.ui_white.assets import BACK_ARROW_WHITE


class NestedNavbar:
    # Navbar with level 2 option buttons which will span and make level 1 buttons move apart.
    # For example if level 1 has 5 buttons with submenu of options 0, 2, 1, 2, 1, then when the 2nd submenu of the second button is chosen, it will be
    # 1
    # [[2]]
    # 2.1
    # [2.2]
    # 3
    # 4
    # 5
    # When the 1st submenu of the 3rd button is chosen, it will be
    # 1
    # 2
    # [[3]]
    # [3.1]
    # 4
    # 5
    # Since the level 1 buttons will move, before clicking the level 1 button we will need to check the current acvive level 1 button and the number of active submenu options to calculate the position of the level 1 button to click.
    def __init__(self, grids: ButtonGrid,
                 subgrid_delta: tuple = None, subgrid_button_shape: tuple = None,
                 subgrid_shapes: List[tuple] = None, direction: str = 'vertical',
                 main_active_color=(57, 189, 255), main_inactive_color=(38, 39, 40),
                 main_active_threshold=221, main_inactive_threshold=221,
                 main_active_count=2000, main_inactive_count=2000,
                 sub_active_color=(125, 126, 126), sub_inactive_color=(38, 39, 40),
                 sub_active_threshold=221, sub_inactive_threshold=221,
                 sub_active_count=500, sub_inactive_count=500, name: str = None):
        """
        Parameters:
            grids (ButtonGrid): The ButtonGrid instance for the main level buttons.
            subbutton (Button): The Button instance for the submenu options.
            subgrid_shapes (list of tuples): A list of grid shapes for each submenu. Each tuple represents the grid shape (rows, cols) for the corresponding submenu.
            main_active_color (tuple): The RGB color for active main buttons.
            main_inactive_color (tuple): The RGB color for inactive main buttons.
            main_active_threshold (int): The threshold for detecting active main buttons.
            main_inactive_threshold (int): The threshold for detecting inactive main buttons.
            main_active_count (int): The minimum count of pixels to confirm an active main button.
            main_inactive_count (int): The maximum count of pixels to confirm an inactive main button.
            sub_active_color (tuple): The RGB color for active submenu options.
            sub_inactive_color (tuple): The RGB color for inactive submenu options.
            sub_active_threshold (int): The threshold for detecting active submenu options.
            sub_inactive_threshold (int): The threshold for detecting inactive submenu options.
            sub_active_count (int): The minimum count of pixels to confirm an active submenu option.
            sub_inactive_count (int): The maximum count of pixels to confirm an inactive submenu option.
        """
        self.grids = grids
        self.subgrid_delta = subgrid_delta if subgrid_delta is not None else grids.delta
        self.subgrid_button_shape = subgrid_button_shape if subgrid_button_shape is not None else grids.button_shape
        self.subgrid_shapes = subgrid_shapes if subgrid_shapes is not None else [(0, 0)] * len(grids.buttons)
        self.direction = direction
        self.main_active_color = main_active_color
        self.main_inactive_color = main_inactive_color
        self.main_active_threshold = main_active_threshold
        self.main_inactive_threshold = main_inactive_threshold
        self.main_active_count = main_active_count
        self.main_inactive_count = main_inactive_count
        self.sub_active_color = sub_active_color
        self.sub_inactive_color = sub_inactive_color
        self.sub_active_threshold = sub_active_threshold
        self.sub_inactive_threshold = sub_inactive_threshold
        self.sub_active_count = sub_active_count
        self.sub_inactive_count = sub_inactive_count
        self.name = name if name is not None else self.grids._name
        self._construct_subgrids()

    def _construct_subgrids(self):
        self.subgrids = []
        for idx, (main_button, subgrid_shape) in enumerate(zip(self.grids.buttons, self.subgrid_shapes)):
            if self.direction == 'vertical':
                subgrid_origin = (main_button.area[0], main_button.area[1] + self.grids.delta[1])
            else:
                subgrid_origin = (main_button.area[0] + self.grids.delta[0], main_button.area[1])
            subgrid = ButtonGrid(origin=subgrid_origin, delta=self.subgrid_delta,
                                 button_shape=self.subgrid_button_shape, grid_shape=subgrid_shape,
                                 name=f'{self.name}_SUB_GRID_{idx}')
            self.subgrids.append(subgrid)

    def is_main_button_active(self, button, main):
        return main.image_color_count(
                    button, color=self.main_active_color, threshold=self.main_active_threshold, count=self.main_active_count)

    def is_main_button_inactive(self, button, main):
        return main.image_color_count(
                    button, color=self.main_inactive_color, threshold=self.main_inactive_threshold, count=self.main_inactive_count)

    def is_subbutton_active(self, button, main):
        return main.image_color_count(
                    button, color=self.sub_active_color, threshold=self.sub_active_threshold, count=self.sub_active_count)

    def is_subbutton_inactive(self, button, main):
        return main.image_color_count(
                    button, color=self.sub_inactive_color, threshold=self.sub_inactive_threshold, count=self.sub_inactive_count)

    def get_info(self, main):
        """
        Get the index of the active main button and the active submenu option.
        Parameters:
            main (ModuleBase): The main module instance to capture screenshots.
        Returns:
            tuple: A tuple containing the index of the active main button and the index of the active submenu option. If no submenu is active, the second element will be None.
        """
        total_main = []
        active_main = []
        total_sub = []
        active_sub = []
        current_offset = (0, 0)
        for index, button in enumerate(self.grids.buttons):
            button._button_offset = area_offset(button._button, offset=current_offset)
            if self.is_main_button_active(button, main=main):
                total_main.append(index)
                active_main.append(index)
                subgrid = self.subgrids[index]
                for sub_index, sub_button in enumerate(subgrid.buttons):
                    if self.is_subbutton_active(sub_button, main=main):
                        total_sub.append((index, sub_index))
                        active_sub.append((index, sub_index))
                    elif self.is_subbutton_inactive(sub_button, main=main):
                        total_sub.append((index, sub_index))
                if self.direction == 'vertical':
                    current_offset = (
                        current_offset[0],
                        current_offset[1] + self.subgrid_button_shape[1] * subgrid.grid_shape[1],
                    )
                else:
                    current_offset = (
                        current_offset[0] + self.subgrid_button_shape[0] * subgrid.grid_shape[0],
                        current_offset[1],
                    )
            elif self.is_main_button_inactive(button, main=main):
                total_main.append(index)

        if len(active_main) == 0:
            active_main_index = None
        elif len(active_main) == 1:
            active_main_index = active_main[0]
        else:
            logger.warning(f'Too many active nav items found in {self.name}, items: {active_main}')
            active_main_index = active_main[0]

        active_sub_index = None
        if active_main_index is not None:
            active_subs_for_active_main = [sub for sub in active_sub if sub[0] == active_main_index]
            if len(active_subs_for_active_main) == 0:
                active_sub_index = None
            elif len(active_subs_for_active_main) == 1:
                active_sub_index = active_subs_for_active_main[0][1]
            else:
                logger.warning(f'Too many active sub nav items found in {self.name} for main index {active_main_index}, items: {active_subs_for_active_main}')
                active_sub_index = active_subs_for_active_main[0][1]

        if len(total_main) < 2:
            logger.warning(f'Too few nav items found in {self.name}, items: {total_main}')
        if len(total_main) == 0:
            main_begin, main_end = None, None
        else:
            main_begin, main_end = total_main[0], total_main[-1]

        return active_main_index, active_sub_index, main_begin, main_end

    def set(self, main: ModuleBase, main_index: int, sub_index: int = None, skip_first_screenshot: bool = False):
        """
        Click the main button and submenu option based on the provided indices.
        Should be used after calling get_info to get the current active main and submenu indices to calculate the position to click.
        Parameters:
            main (ModuleBase): The main module instance to perform clicks and capture screenshots.
            main_index (int): The index of the main button to click. Starts from 0.
            sub_index (int, optional): The index of the submenu option to click. If None, no submenu option will be clicked. Starts from 0.
            skip_first_screenshot (bool):
        """
        logger.info(f'Setting {self.name} to main index {main_index} and sub index {sub_index}')
        click_timer = Timer(2, count=4).reset()
        confirm_timer = Timer(2, count=4).reset()
        for _ in main.loop(skip_first=skip_first_screenshot, timeout=10):
            active_main_index, active_sub_index, main_begin, main_end = self.get_info(main)
            if active_main_index == main_index and (sub_index is None or active_sub_index == sub_index):
                if confirm_timer.reached():
                    logger.info(f'Successfully set {self.name} to main index {main_index} and sub index {sub_index}')
                    return True
                continue
            if active_main_index is None or main_begin is None or main_end is None:
                confirm_timer.reset()
                continue
            if not (main_begin <= main_index <= main_end):
                logger.warning(f'Main index {main_index} out of range for {self.name}, appears ({main_begin}, {main_end})')
                continue
            if click_timer.reached_and_reset():
                if active_main_index != main_index:
                    main.device.click(self.grids.buttons[main_index])
                    confirm_timer.reset()
                else:
                    subgrid = self.subgrids[main_index]
                    if sub_index is not None:
                        main.device.click(subgrid.buttons[sub_index])
                        confirm_timer.reset()
        else:
            logger.warning(f'Failed to set {self.name} to main index {main_index} and sub index {sub_index}')
            return False


class IslandUI(UI):
    def ui_back(self, check_button, appear_button=None, offset=(30, 30), retry_wait=10, skip_first_screenshot=False):
        return self.ui_click(
            click_button=BACK_ARROW_WHITE,
            check_button=check_button,
            appear_button=appear_button,
            offset=offset,
            retry_wait=retry_wait,
            skip_first_screenshot=skip_first_screenshot,
        )

    def has_white_band(self, threshold=1200):
        min_y = 405
        max_y = 560
        image = self.image_crop((0, min_y, 1280, max_y), copy=False)
        luma = rgb2luma(image)
        white_mask = cv2.inRange(luma, 200, 255)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 3))
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
        row_white_width = (white_mask > 0).sum(axis=1)
        candidate_rows = row_white_width > threshold
        min_continuous_height = 50
        count = 0
        for ok in candidate_rows:
            if ok:
                count += 1
                if count >= min_continuous_height:
                    return True
            else:
                count = 0
        return False

    def handle_island_get_items(self):
        if self.appear(GET_ITEMS_1, offset=(20, 20), interval=3):
            self.device.click(ISLAND_CLICK_SAFE_AREA)
            return True
        if self.has_white_band():
            self.device.click(ISLAND_CLICK_SAFE_AREA)
            return True
        return False

    def handle_island_level_up(self):
        if self.appear(ISLAND_LEVEL_UP, offset=(20, 20), interval=3):
            self.device.click(ISLAND_CLICK_SAFE_AREA)
            return True
        return False

    def handle_island_additional(self):
        if self.handle_island_get_items():
            return True
        if self.handle_island_level_up():
            return True
        return False

    def is_button_selected(self, button, color=(57, 189, 255), threshold=221, count=100):
        """
        Detects if the button is surrounded by a blue border,
        which indicates that the button is chosen.

        Args:
            button (Button, tuple): Button instance or area.

        Returns:
            bool: True if the button is chosen, False otherwise.
        """
        if isinstance(button, np.ndarray):
            image = button
        else:
            image = self.image_crop(button, copy=False)
        mask = color_similarity_2d(image, color)
        cv2.inRange(mask, threshold, 255, dst=mask)
        mask[2:-2, 2:-2] = 0
        sum_ = cv2.countNonZero(mask)
        return sum_ > count

    @cached_property
    def _island_manage_side_navbar(self):
        island_manage_side_navbar = ButtonGrid(
            origin=(13, 107), delta=(0, 196/3),
            button_shape=(128, 43), grid_shape=(1, 3)
        )
        return Navbar(grids=island_manage_side_navbar,
                      active_color=(57, 189, 255),
                      inactive_color=(50, 52, 55),
                      active_count=500,
                      inactive_count=500)

    def island_manage_side_navbar_ensure(self, upper=1, skip_first_screenshot=True):
        """
        Args:
            upper (int):
                1 for production,
                2 for restaurant,
                3 for collect
            bottom (int):
                1 for collect,
                2 for restaurant,
                3 for production
        """
        return self._island_manage_side_navbar.set(self, upper=upper, skip_first_screenshot=skip_first_screenshot)
