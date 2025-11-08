from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.handler.assets import POPUP_CONFIRM
from module.logger import logger
from module.shop.assets import *
from module.ui.assets import ACADEMY_GOTO_MUNITIONS, SHOP_BACK_ARROW
from module.ui.navbar import Navbar
from module.ui.page import page_academy, page_munitions
from module.ui.switch import Switch
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
    def shop_nav_250814(self):
        switch = Switch('shop_nav_250814', is_selector=True, offset=(20, 20))
        switch.add_state(NAV_GENERAL, check_button=NAV_GENERAL)
        switch.add_state(NAV_MONTHLY, check_button=NAV_MONTHLY)
        return switch

    @cached_property
    def shop_tab_250814(self):
        switch = Switch('shop_tab_250814', is_selector=True, offset=(20, 20))
        switch.add_state(TAB_GENERAL, check_button=TAB_GENERAL)
        switch.add_state(TAB_MERIT, check_button=TAB_MERIT)
        switch.add_state(TAB_GUILD, check_button=TAB_GUILD)
        switch.add_state(TAB_META, check_button=TAB_META)
        switch.add_state(TAB_PRIZE, check_button=TAB_PRIZE)
        switch.add_state(TAB_CORE_LIMITED, check_button=TAB_CORE_LIMITED)
        switch.add_state(TAB_CORE_MONTHLY, check_button=TAB_CORE_MONTHLY)
        switch.add_state(TAB_MEDAL, check_button=TAB_MEDAL)
        switch.add_state(TAB_PROTOTYPE, check_button=TAB_PROTOTYPE)
        return switch

    def shop_refresh(self):
        """
        Returns:
            bool: If refreshed
        """
        logger.info('Shop refresh')
        refreshed = False

        # SHOP_REFRESH -> POPUP_CONFIRM
        for _ in self.loop():
            if self.appear(POPUP_CONFIRM, offset=(30, 30)):
                break
            if self.appear(SHOP_REFRESH, offset=(30, 30), interval=3):
                # SHOP_REFRESH has two kinds of color when active
                if self.image_color_count(SHOP_REFRESH.button, color=(49, 142, 207), threshold=221, count=50):
                    self.device.click(SHOP_REFRESH)
                    continue
                if self.image_color_count(SHOP_REFRESH.button, color=(54, 117, 161), threshold=221, count=50):
                    self.device.click(SHOP_REFRESH)
                    continue
                if self.image_color_count(SHOP_REFRESH.button, color=(52, 74, 94), threshold=221, count=50):
                    logger.info('Refresh not available')
                    break
                # no `continue`, act like SHOP_REFRESH not matched
                self.interval_clear(SHOP_REFRESH)

        # POPUP_CONFIRM -> SHOP_BACK_ARROW
        for _ in self.loop():
            if self.appear(SHOP_BACK_ARROW, offset=(30, 30)):
                break
            if self.appear(SHOP_BUY_CONFIRM_MISTAKE, interval=3, offset=(200, 200)):
                logger.warning('SHOP_BUY_CONFIRM_MISTAKE')
                self.ui_click(SHOP_CLICK_SAFE_AREA, appear_button=POPUP_CONFIRM, check_button=SHOP_BACK_ARROW,
                              offset=(20, 30), skip_first_screenshot=True)
                refreshed = False
                break
            if self.handle_popup_confirm('SHOP_REFRESH_CONFIRM'):
                refreshed = True
                continue

        self.handle_info_bar()
        return refreshed

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
