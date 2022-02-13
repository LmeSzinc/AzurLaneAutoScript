from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.logger import logger
from module.meowfficer.assets import *
from module.meowfficer.base import MeowfficerBase
from module.meowfficer.buy import MEOWFFICER_COINS
from module.ocr.ocr import DigitCounter
from module.ui.assets import MEOWFFICER_GOTO_DORM

MEOWFFICER_SELECT_GRID = ButtonGrid(
    origin=(770, 245), delta=(130, 147), button_shape=(70, 20), grid_shape=(4, 3),
    name='MEOWFFICER_SELECT_GRID')
MEOWFFICER_FEED_GRID = ButtonGrid(
    origin=(818, 212), delta=(130, 147), button_shape=(30, 30), grid_shape=(4, 3),
    name='MEOWFFICER_FEED_GRID')
MEOWFFICER_FEED = DigitCounter(OCR_MEOWFFICER_FEED, letter=(131, 121, 123), threshold=64)


class MeowfficerEnhance(MeowfficerBase):
    def _meow_select(self, skip_first_screenshot=True):
        """
        Select the target meowfficer in the
        MEOWFFICER_SELECT_GRID (4x3)
        Ensure through dotted yellow/white
        circle appearance after click

        Args:
            skip_first_screenshot (bool):
        """
        # Calculate (x, y) coordinate within
        # MEOWFFICER_SELECT/FEED_GRID (4x3) for
        # enhance target
        index = self.config.Meowfficer_EnhanceIndex - 1
        x = index if index < 4 else index % 4
        y = index // 4

        # Must confirm selected
        # Dotted yellow/white circle
        # around target meowfficer
        click_timer = Timer(3, count=6)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.meow_additional():
                click_timer.reset()
                continue

            if self.image_color_count(MEOWFFICER_SELECT_GRID[x, y], color=(255, 255, 255), threshold=246, count=100):
                break

            if click_timer.reached():
                self.device.click(MEOWFFICER_FEED_GRID[x, y])
                click_timer.reset()

    def meow_feed_scan(self):
        """
        Scan for meowfficers that can be fed
        according to the MEOWFFICER_FEED_GRID (4x3)
        into target meowfficer for enhancement
        Ensure through green check mark apperance
        after click

        Pages:
            in: MEOWFFICER_FEED
            out: MEOWFFICER_FEED

        Returns:
            list(Button)
        """
        clickable = []
        for index, button in enumerate(MEOWFFICER_FEED_GRID.buttons):
            # Exit if 11th button; no need to validate as not
            # possible to click beyond this point
            if index >= 10:
                break

            # Exit if button is empty slot
            if self.image_color_count(button, color=(231, 223, 221), threshold=221, count=450):
                break

            # Continue onto next if button
            # already selected (green check mark)
            if self.image_color_count(button, color=(95, 229, 108), threshold=221, count=150):
                continue

            # Neither base case, so presume
            # button is clickable
            clickable.append(button)

        logger.info(f'Total feed material found: {len(clickable)}')
        return clickable

    def meow_feed_select(self):
        """
        Click and confirm the meowfficers that
        can be used as feed to enhance the target
        meowfficer

        Pages:
            in: MEOWFFICER_FEED
            out: MEOWFFICER_ENHANCE

        Returns:
            int: non-zero positive, some selected
                 zero, none selected
        """
        current = 0
        while 1:
            # Scan for feed, exit if none
            buttons = self.meow_feed_scan()
            if not len(buttons):
                break

            # Else click each button to
            # apply green check mark
            # Sleep for stable image
            for button in buttons:
                self.device.click(button)
            self.device.sleep((0.3, 0.5))
            self.device.screenshot()

            # Exit if maximum clicked
            current, remain, total = MEOWFFICER_FEED.ocr(self.device.image)
            if not remain:
                break

        # Use current to pass appropriate button for ui_click
        # route back to MEOWFFICER_ENHANCE
        logger.info(f'Confirm selected feed material, total: {current} / 10') if current else \
            logger.info('Lack of feed material to complete enhancement, cancelling')
        self.ui_click(MEOWFFICER_FEED_CONFIRM if current else MEOWFFICER_FEED_CANCEL,
                      check_button=MEOWFFICER_ENHANCE_CONFIRM, offset=(20, 20))
        return current

    def meow_enhance_confirm(self, skip_first_screenshot=True):
        """
        Finalize feed materials for enhancement
        of meowfficer

        Pages:
            in: MEOWFFICER_ENHANCE
            out: MEOWFFICER_ENHANCE
        """
        confirm_timer = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(MEOWFFICER_FEED_ENTER, offset=(20, 20)):
                if confirm_timer.reached():
                    break
                continue

            if self.handle_meow_popup_confirm():
                confirm_timer.reset()
                continue
            if self.appear_then_click(MEOWFFICER_ENHANCE_CONFIRM, offset=(20, 20), interval=3):
                confirm_timer.reset()
                continue

    def meow_enhance(self):
        """
        Perform meowfficer enhancement operations
        involving using extraneous meowfficers to
        donate XP into a meowfficer target

        Pages:
            in: page_meowfficer
            out: page_meowfficer
        """
        logger.hr('Meowfficer enhance', level=1)

        # Base Cases
        # - Config at least > 0 but less than or equal to 12
        # - Coins at least > 1000
        if self.config.Meowfficer_EnhanceIndex <= 0 or self.config.Meowfficer_EnhanceIndex > 12:
            logger.warning(f'Meowfficer_EnhanceIndex={self.config.Meowfficer_EnhanceIndex} '
                            'is out of bounds. Please limit to 1~12, skip')
            return

        coins = MEOWFFICER_COINS.ocr(self.device.image)
        if coins < 1000:
            logger.info(f'Coins ({coins}) < 1000. Not enough coins to complete '
                         'enhancement, skip')
            return

        # Select target meowfficer
        # for enhancement
        self._meow_select()

        # Transition to MEOWFFICER_FEED after
        # selection; broken up due to significant
        # delayed behavior of meow_additional
        self.ui_click(MEOWFFICER_ENHANCE_ENTER, check_button=MEOWFFICER_FEED_ENTER,
                      additional=self.meow_additional, retry_wait=3, skip_first_screenshot=True)

        # Initiate feed sequence; loop until exhaust all
        # - Select Feed
        # - Confirm/Cancel Feed
        # - Confirm Enhancement
        # - Check remaining coins after enhancement
        while 1:
            logger.hr('Enhance once', level=2)
            self.ui_click(MEOWFFICER_FEED_ENTER, check_button=MEOWFFICER_FEED_CONFIRM,
                          additional=self.meow_additional, retry_wait=3, skip_first_screenshot=True)
            if not self.meow_feed_select():
                break
            self.meow_enhance_confirm()

            coins = MEOWFFICER_COINS.ocr(self.device.image)
            if coins < 1000:
                logger.info(f'Remaining coins ({coins}) < 1000. Not enough coins for next '
                             'enhancement, skip')
                break

        # Exit back into page_meowfficer
        self.ui_click(MEOWFFICER_GOTO_DORM, check_button=MEOWFFICER_ENHANCE_ENTER,
                      appear_button=MEOWFFICER_ENHANCE_CONFIRM, offset=None)
