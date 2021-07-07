import numpy as np
from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import *
from module.build.assets import *
from module.logger import logger
from module.ui.page import page_build
from module.ui.page_bar import PageBar
from module.ui.ui import UI

BUILD_LOAD_ENSURE_BUTTONS = [SHOP_MEDAL_CHECK, BUILD_SUBMIT_ORDERS, BUILD_FINISH_ORDERS]


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

    @cached_property
    def _build_sidebar(self):
        """
        limited_sidebar 5 options
            build.
            limited_build.
            orders.
            shop.
            retire.

        regular_sidebar 4 options
            build.
            orders.
            shop.
            retire.
        """
        build_sidebar = ButtonGrid(
            origin=(21, 126), delta=(0, 98),
            button_shape=(60, 80), grid_shape=(1, 5),
            name='BUILD_SIDEBAR')

        def additional(total, index):
            if total == 4 and index >= 4:
                index -= 1
            return index

        return PageBar(grid=build_sidebar,
                       inactive_color=(140, 162, 181),
                       additional=additional,
                       name='build_sidebar')

    def build_sidebar_ensure(self, index):
        """
        Ensure able to transition to page and
        page has loaded to completion

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
            bool: bottombar click ensured or not
        """
        if index == 1:
            logger.warning('Transitions to "retire" is not supported')
            return False

        if self._build_sidebar.ensure(self, index) \
                and self.build_load_ensure():
            return True
        return False

    @cached_property
    def _construct_bottombar(self):
        """
        construct_bottombar 4 options
            event.
            light.
            heavy.
            special.
        """
        construct_bottombar = ButtonGrid(
            origin=(262, 615), delta=(209, 0),
            button_shape=(70, 49), grid_shape=(4, 1),
            name='CONSTRUCT_BOTTOMBAR')

        def additional(total, index):
            if total == 3 and index >= 2:
                index -= 1
            return index

        return PageBar(grid=construct_bottombar,
                       inactive_color=(189, 231, 247),
                       additional=additional,
                       is_reversed=True,
                       name='construct_bottombar')

    @cached_property
    def _exchange_bottombar(self):
        """
        exchange_bottombar 2 options
            ships.
            items.
        """
        exchange_bottombar = ButtonGrid(
            origin=(569, 637), delta=(208, 0),
            button_shape=(70, 49), grid_shape=(2, 1),
            name='EXCHANGE_BOTTOMBAR')

        return PageBar(grid=exchange_bottombar,
                       inactive_color=(189, 231, 247),
                       is_reversed=True,
                       name='exchange_bottombar')

    def _build_bottombar(self, is_construct=True):
        """
        Return corresponding PageBar type based on
        parameter 'is_construct'

        Returns:
            PageBar
        """
        if is_construct:
            return self._construct_bottombar
        else:
            return self._exchange_bottombar

    def build_bottombar_ensure(self, index, is_construct=True):
        """
        Ensure able to transition to page and
        page has loaded to completion

        Args:
            index (int):
                construct_bottombar
                1 for event.
                2 for light.
                3 for heavy.
                4 for special.

                exchange_bottombar
                1 for ships.
                2 for items.
            is_construct (bool):

        Returns:
            bool: bottombar click ensured or not
        """
        if self._build_bottombar(is_construct).ensure(self, index) \
                and self.build_load_ensure():
            return True
        return False

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
            is_construct = True if sidebar_index == 5 else False
            if not self.build_sidebar_ensure(sidebar_index) \
                    or not self.build_bottombar_ensure(bottombar_index, is_construct):
                return False
        elif not self.build_sidebar_ensure(sidebar_index):
            return False

        return True
