from module.base.button import ButtonGrid
from module.base.decorator import Config, cached_property
from module.base.timer import Timer
from module.handler.assets import POPUP_CONFIRM
from module.logger import logger
from module.shop.assets import *
from module.ui.assets import ACADEMY_GOTO_MUNITIONS, BACK_ARROW
from module.ui.navbar import Navbar
from module.ui.page import page_academy, page_munitions
from module.ui.ui import UI


class ShopUI(UI):
    @cached_property
    def _shop_bottom_navbar(self):
        """
        Below information relative to after
        shop_swipe
        shop_bottom_navbar 5 options
            medal
            guild.
            prototype.
            core.
            merit.
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
        Below information relative to after
        shop_swipe

        Args:
            left (int): Depends on ship navs
            right (int):

        Returns:
            bool: if bottom_navbar set ensured
        """
        if self._shop_bottom_navbar.set(self, left=left, right=right):
            return True
        return False

    @cached_property
    def shop_tab(self):
        """
        Set with `self.shop_tab.set(main=self, left={index})`
        - index
            1: Monthly shops
            2: General supply shops
        """
        grids = ButtonGrid(
            origin=(340, 93), delta=(189, 0),
            button_shape=(188, 54), grid_shape=(2, 1),
            name='SHOP_TAB')
        return Navbar(
            grids=grids,
            # Yellow bottom dash
            active_color=(255, 219, 83), active_threshold=221, active_count=100,
            # Black bottom dash
            inactive_color=(181, 178, 181), inactive_threshold=221, inactive_count=100,
        )

    @cached_property
    def shop_nav(self):
        """
        Set with `self.shop_nav.set(main=self, upper={index})`
        - index when `shop_tab` is at 1
            1: Core shop (limited items)
            2: Core shop monthly
            3: Medal shop
            4: Prototype shop
        - index when `shop_tab` is at 2
            1: General shop
            2: Merit shop
            3: Guild shop
            4: Meta shop
            5: Gift shop
        """
        grids = ButtonGrid(
            origin=(339, 217), delta=(0, 65),
            button_shape=(15, 64), grid_shape=(1, 5),
            name='SHOP_NAV')
        return Navbar(
            grids=grids,
            # White vertical line to the left of shop names
            active_color=(255, 255, 255), active_threshold=221, active_count=100,
            # Just whatever to make it match
            inactive_color=(49, 56, 82), inactive_threshold=0, inactive_count=100,
        )

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
            if self.appear(SHOP_BUY_CONFIRM_MISTAKE, interval=3, offset=(200, 200)) \
                    and self.appear(POPUP_CONFIRM, offset=(3, 30)):
                self.ui_click(SHOP_CLICK_SAFE_AREA, appear_button=POPUP_CONFIRM, check_button=BACK_ARROW,
                              offset=(20, 30), skip_first_screenshot=True)
                exit_timer.reset()
                refreshed = False
                break
            if self.handle_popup_confirm('SHOP_REFRESH_CONFIRM'):
                exit_timer.reset()
                refreshed = True
                continue

            # End
            if self.appear(BACK_ARROW, offset=(30, 30)):
                if exit_timer.reached():
                    break
            else:
                exit_timer.reset()

        self.handle_info_bar()
        return refreshed

    @Config.when(SERVER='tw')
    def shop_swipe(self, skip_first_screenshot=True):
        """
        Swipes bottom navbar one way, right only

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: True if detected correct exit
                  condition otherwise False
        """
        detection_area = (480, 640, 960, 660)
        swipe_interval = Timer(0.6, count=2)

        for _ in range(3):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Swipe to the left, medal shop on the leftmost and merit shop on the right most
            if self.appear(SHOP_MEDAL_SWIPE_END, offset=(15, 5)) or \
                    self.appear(SHOP_MERIT_SWIPE_END, offset=(15, 5)):
                return True

            if swipe_interval.reached():
                self.device.swipe_vector((480, 0), box=detection_area, random_range=(-50, -10, 50, 10), padding=0)
                swipe_interval.reset()

        return False

    @Config.when(SERVER=None)
    def shop_swipe(self, skip_first_screenshot=True):
        """
        Swipes bottom navbar one way, right only

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: True if detected correct exit
                  condition otherwise False
        """
        detection_area = (480, 640, 960, 660)
        swipe_interval = Timer(0.6, count=2)
        trial = 0

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if trial > 5:
                logger.warning('shop_swipe trail exhausted, assume end reached')
                return False

            # Swipe to the left, medal shop on the leftmost and merit shop on the right most
            if self.appear(SHOP_GIFT_SWIPE_END, offset=(15, 5)) or \
                    self.appear(SHOP_PROTOTYPE_SWIPE_END, offset=(15, 5)):
                return True

            if swipe_interval.reached():
                self.device.swipe_vector((360, 0), box=detection_area, random_range=(-50, -10, 50, 10), padding=0)
                swipe_interval.reset()
                trial += 1

    def ui_goto_shop(self):
        """
        Goes to page_munitions
        This route guarantees start
        in general shop

        Pages:
            in: Any
            out: page_munitions
        """
        if self.ui_get_current_page() == page_munitions:
            logger.info(f'Already at {page_munitions}')
            return

        self.ui_ensure(page_academy)

        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(page_munitions.check_button, offset=(20, 20)):
                break

            # Large offset cause it camera in academy can be move around
            if self.appear_then_click(ACADEMY_GOTO_MUNITIONS, offset=(200, 200), interval=5):
                continue
