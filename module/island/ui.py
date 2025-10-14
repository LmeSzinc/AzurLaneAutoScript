from module.base.timer import Timer
from module.island.assets import *
from module.logger import logger
from module.ocr.ocr import Duration
from module.ui.assets import SHOP_BACK_ARROW
from module.ui.page import page_island_phone
from module.ui.ui import UI


class IslandProductionTime(Duration):
    def after_process(self, result):
        result = super().after_process(result)
        if result == '0:40:00':
            result = '01:40:00'
        return result


OCR_PRODUCTION_TIME = IslandProductionTime(OCR_PRODUCTION_TIME, lang='azur_lane_jp', name='OCR_PRODUCTION_TIME')
OCR_PRODUCTION_TIME_REMAIN = Duration(OCR_PRODUCTION_TIME_REMAIN, name='OCR_PRODUCTION_TIME_REMAIN')


class IslandUI(UI):
    def island_in_management(self, interval=0):
        """
        Args:
            interval (int):

        Returns:
            bool: if in page ISLAND_MANAGEMENT_CHECK
        """
        return self.appear(ISLAND_MANAGEMENT_CHECK, offset=(20, 20), interval=interval)

    def island_management_enter(self):
        """
        Enter island management page.

        Returns:
            bool: if success

        Pages:
            in: page_island_phone
            out: ISLAND_MANAGEMENT_CHECK
        """
        logger.info('Island management enter')
        self.interval_clear(ISLAND_MANAGEMENT_CHECK)
        if self.appear(ISLAND_MANAGEMENT_LOCKED, offset=(20, 20)):
            return False
        self.ui_click(
            click_button=ISLAND_MANAGEMENT,
            check_button=self.island_in_management,
            offset=(20, 20),
            retry_wait=2,
            skip_first_screenshot=True
        )
        return True

    def island_management_quit(self):
        """
        Exit island management page.

        Returns:
            bool: if success

        Pages:
            in: ISLAND_MANAGEMENT_CHECK
            out: page_island_phone
        """
        logger.info('Island management quit')
        self.ui_click(
            click_button=SHOP_BACK_ARROW,
            check_button=page_island_phone.check_button,
            offset=(20, 20),
            retry_wait=2,
            skip_first_screenshot=True
        )
        return True

    def island_product_quit(self):
        """
        Execute quit product page
        """
        logger.info('Island product quit')
        self.interval_clear(ISLAND_MANAGEMENT_CHECK)
        self.ui_click(
            click_button=SHOP_BACK_ARROW,
            check_button=self.island_in_management,
            offset=(20, 20),
            retry_wait=2,
            skip_first_screenshot=True
        )

    def ui_ensure_management_page(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_island_phone or product page
            out: ISLAND_MANAGEMENT_CHECK
        """
        logger.info('UI ensure management page')
        self.interval_clear(ISLAND_MANAGEMENT_CHECK)
        confirm_timer = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.island_in_management():
                if confirm_timer.reached():
                    break
                continue
            else:
                confirm_timer.reset()

            if self.appear_then_click(SHOP_BACK_ARROW, offset=(20, 20), interval=2):
                continue

            if self.appear_then_click(ISLAND_MANAGEMENT, offset=(20, 20), interval=2):
                continue
