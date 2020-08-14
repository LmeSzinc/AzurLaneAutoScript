from module.combat.assets import GET_ITEMS_1
from module.logger import logger
from module.ocr.ocr import Ocr, Digit
from module.reward.assets import *
from module.ui.ui import UI, page_meowfficer, BACK_ARROW_DORM

BUY_MAX = 15
BUY_PRIZE = 1500
MEOWFFICER = Ocr(OCR_MEOWFFICER, letter=(140, 113, 99), threshold=64, alphabet='0123456789/')
MEOWFFICER_CHOOSE = Digit(OCR_MEOWFFICER_CHOOSE, letter=(140, 113, 99), threshold=64)
MEOWDDICER_COINS = Digit(OCR_MEOWDDICER_COINS, letter=(99, 69, 41), threshold=64)


class RewardMeowfficer(UI):
    def moew_choose(self, count):
        """
        Pages:
            in: page_moewfficer
            out: MEOWFFICER_BUY

        Args:
            count (int): 0 to 15.

        Returns:
            bool: If success.
        """
        remain = MEOWFFICER.ocr(self.device.image)
        if '/' not in remain:
            logger.warning('Unexpected OCR result')
            return False
        remain = int(remain.split('/')[0])
        logger.attr('Meowfficer_remain', remain)

        # Check buy status
        if remain <= BUY_MAX - count:
            logger.info('Already bought today')
            return False
        elif remain < count:
            logger.info('Remain less than to buy')
            count = remain
        # Check coins
        coins = MEOWDDICER_COINS.ocr(self.device.image)
        if coins < BUY_PRIZE:
            logger.warning('Not enough coins to buy one')
            return False
        elif (count - int(remain == BUY_MAX)) * BUY_PRIZE > coins:
            count = coins // BUY_PRIZE + int(remain == BUY_MAX)
            logger.warning(f'Current coins only enough to buy {count}')

        self.ui_click(MEOWFFICER_BUY_ENTER, check_button=MEOWFFICER_BUY, skip_first_screenshot=True)
        self.ui_ensure_index(count, letter=MEOWFFICER_CHOOSE, prev_button=MEOWFFICER_BUY_PREV,
                             next_button=MEOWFFICER_BUY_NEXT, skip_first_screenshot=True)
        return True

    def meow_confirm(self, skip_first_screenshot=True):
        """
        Pages:
            in: MEOWFFICER_BUY
            out: page_moewfficer
        """
        executed = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(MEOWFFICER_BUY,  interval=5):
                continue
            if self.appear_then_click(MEOWFFICER_BUY_CONFIRM, interval=5):
                continue
            if self.appear_then_click(MEOWFFICER_BUY_SKIP, interval=5):
                continue
            if self.appear(GET_ITEMS_1):
                self.device.click(MEOWFFICER_BUY_SKIP)
                executed = True
                continue

            # End
            if executed and self.appear(MEOWFFICER_BUY):
                break

        self.ui_click(BACK_ARROW_DORM, check_button=MEOWFFICER_BUY_ENTER, appear_button=MEOWFFICER_BUY, offset=None)

    def meow_buy(self):
        """
        Pages:
            in: Any page
            out: page_main
        """
        self.ui_ensure(page_meowfficer)
        if self.moew_choose(count=self.config.BUY_MEOWFFICER):
            self.meow_confirm()
        self.ui_goto_main()

    def handle_meowfficer(self):
        """
        Returns:
            bool: If executed
        """
        if self.config.BUY_MEOWFFICER < 1:
            return False
        if self.config.record_executed_since(option=('RewardRecord', 'meowfficer'), since=(0,)):
            return False

        self.meow_buy()

        self.config.record_save(option=('RewardRecord', 'meowfficer'))
        return True
