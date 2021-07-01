from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.base.utils import random_rectangle_vector
from module.logger import logger
from module.shop.assets import *
from module.ui.assets import BACK_ARROW
from module.ui.page import page_munitions
from module.ui.ui import UI

SHOP_LOAD_ENSURE_BUTTONS = [SHOP_GENERAL_CHECK, SHOP_GUILD_CHECK,
                            SHOP_MERIT_CHECK, SHOP_PROTOTYPE_CHECK,
                            SHOP_CORE_CHECK]

SHOP_BOTTOMBAR = ButtonGrid(
    origin=(393, 637), delta=(182, 0), button_shape=(45, 15), grid_shape=(5, 1), name='SHOP_BOTTOMBAR')


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
            results = [self.appear(button) for button in SHOP_LOAD_ENSURE_BUTTONS]
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

    def _shop_bottombar_click(self, index):
        """
        Performs the calculations necessary
        to determine the index location on
        bottombar and then click at that location

        Args:
            index (int):
                5 for guild.
                4 for prototype.
                3 for core.
                2 for merit.
                1 for general.

        Returns:
            bool: if changed.
        """
        if index <= 0 or index > 5:
            logger.warning(f'Bottombar index cannot be clicked, {index}, limit to 1 through 5 only')
            return False

        current = 0
        total = 0

        for idx, button in enumerate(SHOP_BOTTOMBAR.buttons()):
            total = idx + 1
            if self.image_color_count(button, color=(33, 195, 239), threshold=235, count=30):
                current = total

        if not current:
            # No current, may appear erroneous but
            # able to recover
            logger.info('No shop bottombar active.')
        if total == 3:
            current = 4 - current
        elif total == 4:
            current = 5 - current
        elif total == 5:
            current = 6 - current
        else:
            logger.warning('Shop bottombar total count error.')

        logger.attr('Shop_bottombar', f'{current}/{total}')
        if current == index:
            return False

        diff = total - index
        if diff >= 0:
            self.device.click(SHOP_BOTTOMBAR[diff, 0])
        else:
            logger.warning(f'Target index {index} cannot be clicked')
        return True

    def shop_bottombar_ensure(self, index, skip_first_screenshot=True):
        """
        Performs action to ensure the specified
        index bottombar is transitioned into
        Maximum of 3 attempts

        Args:
            index (int):
                5 for guild.
                4 for prototype.
                3 for core.
                2 for merit.
                1 for general.
            skip_first_screenshot (bool):

        Returns:
            bool: bottombar click ensured or not
        """
        if index <= 0 or index > 5:
            logger.warning(f'Bottombar index cannot be ensured, {index}, limit 1 through 5 only')
            return False

        counter = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._shop_bottombar_click(index):
                if counter >= 2:
                    logger.warning('Bottombar could not be ensured')
                    return False
                counter += 1
                self.device.sleep((0.5, 0.8))
                continue
            else:
                if not self.shop_load_ensure():
                    return False
                return True

    def shop_refresh(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot: bool

        Returns:
            bool: If refreshed
        """
        refreshed = False
        if not self.appear(SHOP_REFRESH):
            return refreshed

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
        Swipes bottombar one way, right only

        Args:
            bool: skip_first_screenshot

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

            if self.appear(SHOP_GUILD_SWIPE_END, offset=(5, 5)) or \
               self.appear(SHOP_GENERAL_SWIPE_END, offset=(5, 5)):
                return True

            backup = self.config.cover(DEVICE_CONTROL_METHOD='minitouch')
            p1, p2 = random_rectangle_vector(
                (480, 0), box=detection_area, random_range=(-50, -50, 50, 50), padding=20)
            self.device.drag(p1, p2, segments=2, shake=(0, 25), point_random=(0, 0, 0, 0), shake_random=(0, -5, 0, 5))
            backup.recover()
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
