import numpy as np
from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.base.utils import *
from module.build.assets import *
from module.logger import logger
from module.ui.page import page_build
from module.ui.ui import UI

BUILD_LOAD_ENSURE_BUTTONS = [SHOP_MEDAL_CHECK, BUILD_SUBMIT_ORDERS, BUILD_FINISH_ORDERS]

BUILD_SIDEBAR = ButtonGrid(
    origin=(21, 126), delta=(0, 98), button_shape=(60, 80), grid_shape=(1, 5), name='BUILD_SIDEBAR')

BUILD_BOTTOMBAR = ButtonGrid(
    origin=(133, 612), delta=(208, 0), button_shape=(203, 51), grid_shape=(4, 1), name='BUILD_BOTTOMBAR')

SHOP_BOTTOMBAR = ButtonGrid(
    origin=(436, 636), delta=(208.5, 0), button_shape=(203, 51), grid_shape=(2, 1), name='SHOP_BOTTOMBAR')


class BuildUI(UI):
    def build_load_ensure(self, skip_first_screenshot=True):
        """
        Switching between sidebar clicks for some
        takes a bit of processing before fully loading
        like guild logistics

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: Whether expected assets loaded completely
        """
        confirm_timer = Timer(1.5, count=3).start()
        ensure_timeout = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            results = [self.appear(button) for button in BUILD_LOAD_ENSURE_BUTTONS]
            if any(results):
                if confirm_timer.reached():
                    return True
                ensure_timeout.reset()
                continue
            confirm_timer.reset()

            # Exception
            if ensure_timeout.reached():
                logger.warning('Wait for loaded assets is incomplete, ensure not guaranteed')
                return False

    def _build_sidebar_click(self, index):
        """
        Performs the calculations necessary
        to determine the index location on
        sidebar and then click at that location

        Args:
            index (int):
                limited sidebar
                5 for build.
                4 for limited_build.
                3 for orders.
                2 for shop.
                1 for retire.

                regular sidebar
                5   for build.
                3/4 for orders.
                2   for shop.
                1   for retire.

        Returns:
            bool: if changed.
        """
        if index <= 0 or index > 5:
            logger.warning(f'Sidebar index cannot be clicked, {index}, limit to 1 through 5 only')
            return False

        current = 0
        total = 0

        for idx, button in enumerate(BUILD_SIDEBAR.buttons()):
            image = np.array(self.image_area(button))
            if np.sum(image[:, :, 0] > 235) > 100:
                current = idx + 1
                total = idx + 1
                continue
            if np.sum(color_similarity_2d(image, color=(140, 162, 181)) > 221) > 100:
                total = idx + 1
            else:
                break
        if not current:
            logger.warning('No build sidebar active.')
        if total == 3:
            current = 4 - current
        elif total == 4:
            current = 5 - current
        elif total == 5:
            current = 6 - current
        else:
            logger.warning('Build sidebar total count error.')

        # This is a regular sidebar, decrement
        # the index by 1 if requested 4 or greater
        if total == 4 and index >= 4:
            index -= 1

        logger.attr('Build_sidebar', f'{current}/{total}')
        if current == index:
            return False

        diff = total - index
        if index == 1:
            logger.warning('Retire sidebar option is not supported')
        elif diff >= 0:
            self.device.click(BUILD_SIDEBAR[0, diff])
        else:
            logger.warning(f'Target index {index} cannot be clicked')
        return True

    def build_sidebar_ensure(self, index, skip_first_screenshot=True):
        """
        Performs action to ensure the specified
        index sidebar is transitioned into
        Maximum of 3 attempts

        Args:
            index (int):
                limited sidebar
                5 for build.
                3 for limited_build.
                4 for orders.
                2 for exchange.
                1 for retire.

                regular sidebar
                5   for build.
                3/4 for orders.
                2   for exchange.
                1   for retire.
            skip_first_screenshot (bool):

        Returns:
            bool: sidebar click ensured or not
        """
        if index <= 0 or index > 5:
            logger.warning(f'Sidebar index cannot be ensured, {index}, limit 1 through 5 only')
            return False

        counter = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._build_sidebar_click(index):
                if counter >= 2:
                    logger.warning('Sidebar could not be ensured')
                    return False
                counter += 1
                self.device.sleep((0.5, 0.8))
                continue
            else:
                if not self.build_load_ensure():
                    return False
                return True

    def _build_bottombar_click(self, index, grid):
        """
        Performs the calculations necessary
        to determine the index location on
        bottombar and then click at that location

        Args:
            index (int):
                build_sidebar
                1 for event.
                2 for light.
                3 for heavy.
                4 for special.

                shop_sidebar
                1 for ships.
                2 for items.

        Returns:
            bool: if changed.
        """
        if index <= 0 or index > 4:
            logger.warning(f'Bottombar index cannot be clicked, {index}, limit to 1 through 4 only')
            return False

        current = 0
        total = 0

        buttons = grid.buttons()
        buttons.reverse()
        for idx, button in enumerate(buttons):
            image = np.array(self.image_area(button))
            if np.sum(image[:, :, 0] > 235) > 100:
                current = idx + 1
                total = idx + 1
                continue
            if np.sum(color_similarity_2d(image, color=(214, 235, 255)) > 221) > 100:
                total = idx + 1
            else:
                break
        if not current:
            logger.warning('No build bottombar active.')
        if total == 2:
            current = 3 - current
        elif total == 3:
            current = 4 - current
        elif total == 4:
            current = 5 - current
        else:
            logger.warning('Build bottombar total count error.')

        if total == 3 and index >= 2:
            index -= 1

        logger.attr('Build_bottombar', f'{current}/{total}')
        if current == index:
            return False

        diff = total - index
        if diff >= 0:
            self.device.click(buttons[diff])
        else:
            logger.warning(f'Target index {index} cannot be clicked')
        return True

    def build_bottombar_ensure(self, sidebar_index, bottombar_index, skip_first_screenshot=True):
        """
        Performs action to ensure the specified
        index bottombar is transitioned into
        Maximum of 3 attempts

        Args:
            sidebar_index (int):
                only allow 5 (build) or 2 (shop), the only UIs which have a bottombar

            bottombar_index (int):
                build_sidebar
                1 for event.
                2 for light.
                3 for heavy.
                4 for special.

                shop_sidebar
                1 for ships.
                2 for items.
            skip_first_screenshot (bool):

        Returns:
            bool: bottombar click ensured or not
        """
        if sidebar_index != 5 and sidebar_index != 2:
            return False

        if not self.build_sidebar_ensure(sidebar_index):
            return False

        if sidebar_index == 5:
            if bottombar_index <= 0 or bottombar_index > 4:
                logger.warning(f'Bottombar index for build sidebar cannot be ensured, {index}, limit 1 through 4 only')
                return False
            bottombar = BUILD_BOTTOMBAR
        else:
            if bottombar_index <= 0 or bottombar_index > 2:
                logger.warning(f'Bottombar index for shop sidebar cannot be ensured, {index}, limit 1 through 2 only')
                return False
            bottombar = SHOP_BOTTOMBAR

        counter = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._build_bottombar_click(bottombar_index, bottombar):
                if counter >= 2:
                    logger.warning('Bottombar could not be ensured')
                    return False
                counter += 1
                self.device.sleep((0.5, 0.8))
                continue
            else:
                return True

    def ui_goto_build(self, sidebar_index, bottombar_index):
        """
        Ensures ui is at desired position/option utilizes
        sidebar and bottombar when necessary
        Some options may have significant load times
        until interactable

        Args:
            sidebar_index (int): refer to build_sidebar_ensure
            bottombar_index (int): refer to build_bottombar_ensure

        Returns:
            bool: If successful
        """
        self.ui_ensure(destination=page_build)

        if sidebar_index == 5 or sidebar_index == 2:
            if not self.build_bottombar_ensure(sidebar_index, bottombar_index):
                return False
        elif not self.build_sidebar_ensure(sidebar_index):
            return False

        return True
