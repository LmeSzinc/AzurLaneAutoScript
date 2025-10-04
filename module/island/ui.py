from datetime import timedelta

from module.island.assets import *
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
        Pages:
            in: page_island_phone
            out: ISLAND_MANAGEMENT_CHECK
        """
        self.interval_clear(ISLAND_MANAGEMENT_CHECK)
        self.ui_click(
            click_button=ISLAND_MANAGEMENT,
            check_button=self.island_in_management,
            offset=(20, 20),
            retry_wait=2,
            skip_first_screenshot=True
        )

    def island_management_quit(self):
        """
        Pages:
            in: ISLAND_MANAGEMENT_CHECK
            out: page_island_phone
        """
        self.ui_click(
            click_button=SHOP_BACK_ARROW,
            check_button=page_island_phone.check_button,
            offset=(20, 20),
            retry_wait=2,
            skip_first_screenshot=True
        )

    def island_product_quit(self):
        """
        Execute quit product page
        """
        self.interval_clear(ISLAND_MANAGEMENT_CHECK)
        self.ui_click(
            click_button=SHOP_BACK_ARROW,
            check_button=self.island_in_management,
            offset=(20, 20),
            retry_wait=2,
            skip_first_screenshot=True
        )
