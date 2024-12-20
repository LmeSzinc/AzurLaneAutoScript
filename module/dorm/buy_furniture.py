from datetime import datetime, timedelta

from module.combat.assets import GET_SHIP
from module.dorm.assets import *
from module.exercise.assets import EXERCISE_PREPARATION
from module.logger import logger
from module.ocr.ocr import Digit
from module.ui.assets import DORM_CHECK
from module.ui.ui import UI

OCR_FURNITURE_COIN = Digit(OCR_DORM_FURNITURE_COIN, letter=(107, 89, 82), threshold=128, alphabet='0123456789', name='OCR_FURNITURE_COIN')
OCR_FURNITURE_PRICE = Digit(OCR_DORM_FURNITURE_PRICE, letter=(255, 247, 247), threshold=64, alphabet='0123456789', name='OCR_FURNITURE_PRICE')

CHECK_INTERVAL = 6  # Check every 6 days
# Only for click
FURNITURE_BUY_BUTTON = {
    "all": DORM_FURNITURE_BUY_ALL,
    "set": DORM_FURNITURE_BUY_SET
}


class BuyFurniture(UI):
    def enter_first_furniture_details_page(self, skip_first_screenshot=False):
        """
        Pages:
            in: page_dorm or DORM_FURNITURE_SHOP_ENTER(furniture shop page)
            out: 
        """
        self.interval_clear((DORM_CHECK, DORM_FURNITURE_DETAILS_ENTER,
                             DORM_FURNITURE_SHOP_FIRST,))
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Enter furniture shop page from page_dorm, only need to enter once
            if self.appear(DORM_CHECK, offset=(20, 20), interval=3):
                self.device.click(DORM_FURNITURE_SHOP_ENTER)
                self.interval_reset([GET_SHIP, EXERCISE_PREPARATION])
                continue

            if self.appear(DORM_FURNITURE_SHOP_FIRST_SELECTED, offset=(20, 20)):
                self.interval_reset([GET_SHIP, EXERCISE_PREPARATION])
                # Enter furniture details page from furniture shop page
                if self.appear(DORM_FURNITURE_DETAILS_ENTER, offset=(20, 20), interval=3):
                    self.device.click(DORM_FURNITURE_DETAILS_ENTER)
                    continue
            # After buy furniture, current furniture in store not first on list below.
            # Re select the first piece of furniture on left side of furniture list below.
            elif self.appear(DORM_FURNITURE_SHOP_FIRST, offset=(20, 20), interval=3):
                self.device.click(DORM_FURNITURE_SHOP_FIRST)
                self.interval_reset([GET_SHIP, EXERCISE_PREPARATION])
                continue

            if self.appear(DORM_FURNITURE_DETAILS_QUIT, offset=(20, 20)):
                break

            if self.ui_additional():
                self.interval_clear(DORM_CHECK)
                continue

    def furniture_shop_quit(self, skip_first_screenshot=False):
        """
        Pages:
            in: DORM_FURNITURE_DETAILS_ENTER (furniture shop page)
            out: page_dorm
        """
        self.interval_clear(DORM_FURNITURE_DETAILS_ENTER)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(DORM_CHECK, offset=(20, 20)):
                break

            if self.appear(DORM_FURNITURE_DETAILS_ENTER, offset=(20, 20), interval=3):
                self.device.click(DORM_FURNITURE_SHOP_QUIT)
                continue

    def furniture_details_page_quit(self, skip_first_screenshot=False):
        """
        Pages:
            in: DORM_FURNITURE_DETAILS_QUIT (furniture details page)
            out: DORM_FURNITURE_DETAILS_ENTER (furniture shop page)
        """
        self.interval_clear(DORM_FURNITURE_DETAILS_QUIT)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(DORM_FURNITURE_DETAILS_ENTER, offset=(20, 20)):
                break

            if self.appear(DORM_FURNITURE_DETAILS_QUIT, offset=(20, 20), interval=3):
                self.device.click(DORM_FURNITURE_DETAILS_QUIT)
                continue

    def furniture_payment_enter(self, buy_button: Button, skip_first_screenshot=False):
        """
        Args:
            buy_button(Button): It can only be
                                DORM_FURNITURE_BUY_SET or DORM_FURNITURE_BUY_ALL

        Page:
            in: DORM_FURNITURE_DETAILS_QUIT (furniture details page)
            out: DORM_FURNITURE_BUY_CONFIRM (furniture payment page)
        """
        self.interval_clear(DORM_FURNITURE_DETAILS_QUIT)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(DORM_FURNITURE_BUY_CONFIRM):
                break

            if self.appear(DORM_FURNITURE_DETAILS_QUIT, interval=3):
                self.device.click(buy_button)

    def buy_furniture_confirm(self, skip_first_screenshot=False):
        """
        Click DORM_FURNITURE_BUY_CONFIRM and back to furniture details page

        Pages:
            in: DORM_FURNITURE_BUY_CONFIRM (furniture payment page)
            out: DORM_FURNITURE_DETAILS_QUIT (furniture details page)
        """
        self.interval_clear(DORM_FURNITURE_BUY_CONFIRM)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(DORM_FURNITURE_DETAILS_QUIT):
                break

            if self.appear(DORM_FURNITURE_BUY_CONFIRM, offset=(20, 20), interval=3):
                self.device.click(DORM_FURNITURE_BUY_CONFIRM)

    def buy_furniture_once(self, buy_option: str):
        """
        Args:
            buy_option(str): It can only be "all" or "set"
                             depend on config.BuyFurniture_BuyOption
        Returns:
            bool: True if furniture coin > furniture price, else False

        Pages:
            in: DORM_FURNITURE_DETAILS_QUIT (furniture details page)
        """
        buy_button: Button = FURNITURE_BUY_BUTTON[buy_option]
        coin = OCR_FURNITURE_COIN.ocr(self.device.image)

        self.furniture_payment_enter(buy_button, skip_first_screenshot=True)
        price = OCR_FURNITURE_PRICE.ocr(self.device.image)

        # Successful or failed buy will have popup and back to furniture details page,
        # produce the result from furniture coin compare to furniture price.
        if coin >= price > 0:
            logger.info(f"Enough furniture coin, buy {buy_option}")
            buy_successful = True
        else:
            logger.info(f"Not enough furniture coin, purchase is over")
            buy_successful = False
        self.buy_furniture_confirm(skip_first_screenshot=True)
        self.furniture_details_page_quit(skip_first_screenshot=True)
        return buy_successful

    def _buy_furniture_run(self):
        """
        Enter first furniture details page and check furniture is time-limited,
        if appear countdown, buy this furniture.
        Return:
            bool: True if Successfully bought,
                  False if Failed buy
        """
        self.enter_first_furniture_details_page()
        if self.match_template_color(DORM_FURNITURE_COUNTDOWN, offset=(20, 20)):
            logger.info("There is a time-limited furniture available for buy")

            if self.buy_furniture_once(self.config.BuyFurniture_BuyOption):
                logger.info("Find next time-limited furniture")
                return True  # continue
            else:
                return False  # break
        else:
            logger.info("No time-limited furniture found")
            return False  # break

    def buy_furniture_run(self):
        """
        Pages:
            in: DORM_FURNITURE_DETAILS_ENTER (furniture shop page)
            out: page_dorm
        """
        logger.info("Buy furniture run")
        while 1:
            if self._buy_furniture_run():
                continue
            else:
                break
        # Quit to page_dorm
        logger.info("Fallback to dorm_page")
        self.furniture_details_page_quit(skip_first_screenshot=True)
        self.furniture_shop_quit(skip_first_screenshot=True)
        self.config.BuyFurniture_LastRun = datetime.now().replace(microsecond=0)

    def run(self):
        """
        Run Buy Furniture
        """
        logger.attr("BuyFurniture_LastRun", self.config.BuyFurniture_LastRun)
        logger.attr("CHECK_INTERVAL", CHECK_INTERVAL)

        time_run = self.config.BuyFurniture_LastRun + timedelta(days=CHECK_INTERVAL)
        logger.info(f"Task BuyFurniture run time is {time_run}")

        if datetime.now().replace(microsecond=0) < time_run:
            logger.info("Not running time, skip")
            return

        self.buy_furniture_run()
