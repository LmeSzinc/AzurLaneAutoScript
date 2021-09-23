from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import *
from module.logger import logger
from module.shop.assets import *
from module.ui.assets import BACK_ARROW
from module.ui.navbar import Navbar
from module.ui.page import page_munitions
from module.ui.ui import UI

SHOP_LOAD_ENSURE_BUTTONS = [SHOP_GENERAL_CHECK, SHOP_GUILD_CHECK,
                            SHOP_MERIT_CHECK, SHOP_PROTOTYPE_CHECK,
                            SHOP_CORE_CHECK]


class ShopUI(UI):
    def shop_load_ensure(self, skip_first_screenshot=True):
        """
        Switching between bottombar clicks for some
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
            results = [self.appear(button, offset=(100, 50)) for button in SHOP_LOAD_ENSURE_BUTTONS]
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
    def _shop_bottom_navbar(self):
        """
        shop_bottom_navbar 5 options
            guild.
            prototype.
            core.
            merit.
            general.
        """
        shop_bottom_navbar = ButtonGrid(
            origin=(399, 619), delta=(182, 0),
            button_shape=(56, 42), grid_shape=(5, 1),
            name='SHOP_BOTTOM_NAVBAR')

        return Navbar(grids=shop_bottom_navbar,
                      active_color=(33, 195, 239),
                      inactive_color=(181, 178, 181))

    def shop_bottom_navbar_ensure(self, left=None, right=None):
        """
        Ensure able to transition to page and
        page has loaded to completion

        Args:
            left (int):
                1 for guild.
                4 for prototype.
                3 for core.
                2 for merit.
                1 for general.
            right (int):
                5 for guild.
                4 for prototype.
                3 for core.
                2 for merit.
                1 for general.

        Returns:
            bool: if bottom_navbar set ensured
        """
        if self._shop_bottom_navbar.set(self, left=left, right=right) \
                and self.shop_load_ensure():
            return True
        return False

    def shop_refresh(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot: bool

        Returns:
            bool: If refreshed
        """
        refreshed = False
        exit_timer = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(SHOP_REFRESH, interval=3):
                exit_timer.reset()
                continue
            if self.handle_popup_confirm('SHOP_REFRESH_CONFIRM'):
                exit_timer.reset()
                refreshed = True
                continue

            # End
            if self.appear(BACK_ARROW, offset=(20, 20)):
                if exit_timer.reached():
                    break
            else:
                exit_timer.reset()

        self.handle_info_bar()
        return refreshed

    def _shop_swipe(self, skip_first_screenshot=True):
        """
        Swipes bottom navbar one way, right only

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: True if detected correct exit
                  condition otherwise False
        """
        detection_area = (480, 640, 960, 660)

        for _ in range(5):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(SHOP_GUILD_SWIPE_END, offset=(15, 5)) or \
                    self.appear(SHOP_GENERAL_SWIPE_END, offset=(15, 5)):
                return True

            # backup = self.config.cover(DEVICE_CONTROL_METHOD='minitouch')
            p1, p2 = random_rectangle_vector(
                (480, 0), box=detection_area, random_range=(-50, -50, 50, 50), padding=20)
            self.device.drag(p1, p2, segments=2, shake=(0, 25), point_random=(0, 0, 0, 0), shake_random=(0, -5, 0, 5))
            # backup.recover()
            self.device.sleep(0.3)

        return False

    def ui_goto_shop(self):
        """
        Goes to page_munitions and
        swipes if needed
        Default view defined as
        screen appears with
        guild shop as left-most or
        general shop as right-most

        Returns:
            bool: True if in expected view
                  otherwise False
        """
        self.ui_ensure(page_munitions)

        return self._shop_swipe()
