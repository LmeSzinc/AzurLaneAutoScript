from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.gacha.assets import *
from module.logger import logger
from module.ui.navbar import Navbar
from module.ui.page import page_build
from module.ui.ui import UI

GACHA_LOAD_ENSURE_BUTTONS = [SHOP_MEDAL_CHECK, BUILD_SUBMIT_ORDERS, BUILD_SUBMIT_WW_ORDERS, BUILD_FINISH_ORDERS, BUILD_WW_CHECK]


class GachaUI(UI):
    def gacha_load_ensure(self, skip_first_screenshot=True):
        """
        Switching between sidebar clicks for some
        takes a bit of processing before fully loading
        like guild logistics

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: Whether expected assets loaded completely
        """
        ensure_timeout = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            results = [self.appear(button) for button in GACHA_LOAD_ENSURE_BUTTONS]
            if any(results):
                return True

            # Exception
            if ensure_timeout.reached():
                logger.warning('Wait for loaded assets is incomplete, ensure not guaranteed')
                return False

    @cached_property
    def _gacha_side_navbar(self):
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
        gacha_side_navbar = ButtonGrid(
            origin=(21, 126), delta=(0, 98),
            button_shape=(60, 80), grid_shape=(1, 5),
            name='GACHA_SIDE_NAVBAR')

        return Navbar(grids=gacha_side_navbar,
                      active_color=(247, 255, 173), active_threshold=221,
                      inactive_color=(140, 162, 181), inactive_threshold=221)

    def gacha_side_navbar_ensure(self, upper=None, bottom=None):
        """
        Ensure able to transition to page and
        page has loaded to completion

        Args:
            upper (int):
            limited|regular
                1     for build.
                2|N/A for limited_build.
                3|2   for orders.
                4|3   for shop.
                5|4   for retire.
            bottom (int):
            limited|regular
                5|4   for build.
                4|N/A for limited_build.
                3     for orders.
                2     for shop.
                1     for retire.

        Returns:
            bool: if side_navbar set ensured
        """
        retire_upper = 5 if self._gacha_side_navbar.get_total(main=self) == 5 else 4
        if upper == retire_upper or bottom == 1:
            logger.warning('Transitions to "retire" is not supported')
            return False

        if self._gacha_side_navbar.set(self, upper=upper, bottom=bottom) \
                and self.gacha_load_ensure():
            return True
        return False

    @cached_property
    def _construct_bottom_navbar(self):
        """
        limited 4 options
            build.
            limited_build.
            orders.
            shop.
            retire.

        regular 3 options
            build.
            orders.
            shop.
            retire.
        """
        construct_bottom_navbar = ButtonGrid(
            origin=(262, 615), delta=(209, 0),
            button_shape=(70, 49), grid_shape=(4, 1),
            name='CONSTRUCT_BOTTOM_NAVBAR')

        return Navbar(grids=construct_bottom_navbar,
                      active_color=(247, 227, 148),
                      inactive_color=(189, 231, 247))

    @cached_property
    def _exchange_bottom_navbar(self):
        """
        2 options
            ships.
            items.
        """
        exchange_bottom_navbar = ButtonGrid(
            origin=(569, 637), delta=(208, 0),
            button_shape=(70, 49), grid_shape=(2, 1),
            name='EXCHANGE_BOTTOM_NAVBAR')

        return Navbar(grids=exchange_bottom_navbar,
                      active_color=(247, 227, 148),
                      inactive_color=(189, 231, 247))

    def _gacha_bottom_navbar(self, is_build=True):
        """
        Return corresponding Navbar type based on
        parameter 'is_build'

        Returns:
            Navbar
        """
        if is_build:
            return self._construct_bottom_navbar
        else:
            return self._exchange_bottom_navbar

    def gacha_bottom_navbar_ensure(self, left=None, right=None, is_build=True):
        """
        Ensure able to transition to page and
        page has loaded to completion

        Args:
            left (int):
                construct_bottom_navbar
                limited|regular
                1|N/A for event.
                2|1   for light.
                3|2   for heavy.
                4|3   for special.

                exchange_bottom_navbar
                1     for ships.
                2     for items.
            right (int):
                construct_bottom_navbar
                limited|regular
                4|N/A for event.
                3     for light.
                2     for heavy.
                1     for special.

                exchange_bottom_navbar
                2     for ships.
                1     for items.
            is_build (bool):

        Returns:
            bool: if bottom_navbar set ensured
        """
        gacha_bottom_navbar = self._gacha_bottom_navbar(is_build)
        if is_build and gacha_bottom_navbar.get_total(main=self) == 3:
            if left == 1 or right == 4:
                logger.info('Construct event not available, default to light')
                left = 1
                right = None
            if left == 4:
                left = 3

        if gacha_bottom_navbar.set(self, left=left, right=right) \
                and self.gacha_load_ensure():
            return True
        return False

    def ui_goto_gacha(self):
        self.ui_ensure(page_build)


if __name__ == '__main__':
    self = GachaUI('alas')
    self.image_file = r'C:\Users\LmeSzinc\Nox_share\ImageShare\Screenshots\Screenshot_20220224-182355.png'
    res = self._gacha_side_navbar.get_info(main=self)
    print(res)