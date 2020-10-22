from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from module.reward.assets import *
from module.ui.ui import UI, page_meowfficer, MEOWFFICER_GOTO_DORM

BUY_MAX = 15
BUY_PRIZE = 1500
MEOWFFICER = DigitCounter(OCR_MEOWFFICER, letter=(140, 113, 99), threshold=64)
MEOWFFICER_CHOOSE = Digit(OCR_MEOWFFICER_CHOOSE, letter=(140, 113, 99), threshold=64)
MEOWFFICER_COINS = Digit(OCR_MEOWFFICER_COINS, letter=(99, 69, 41), threshold=64)


class RewardMeowfficer(UI):
    def meow_choose(self, count):
        """
        Pages:
            in: page_meowfficer
            out: MEOWFFICER_BUY

        Args:
            count (int): 0 to 15.

        Returns:
            bool: If success.
        """
        remain, _, _ = MEOWFFICER.ocr(self.device.image)
        logger.attr('Meowfficer_remain', remain)

        # Check buy status
        if remain <= BUY_MAX - count:
            logger.info('Already bought today')
            return False
        elif remain < count:
            logger.info('Remain less than to buy')
            count = remain
        # Check coins
        coins = MEOWFFICER_COINS.ocr(self.device.image)
        if (coins < BUY_PRIZE) and (remain < BUY_MAX):
            logger.warning('Not enough coins to buy one')
            return False
        elif (count - int(remain == BUY_MAX)) * BUY_PRIZE > coins:
            count = coins // BUY_PRIZE + int(remain == BUY_MAX)
            logger.warning(f'Current coins only enough to buy {count}')

        self.ui_click(MEOWFFICER_BUY_ENTER, check_button=MEOWFFICER_BUY, skip_first_screenshot=True)
        self.ui_ensure_index(count, letter=MEOWFFICER_CHOOSE, prev_button=MEOWFFICER_BUY_PREV,
                             next_button=MEOWFFICER_BUY_NEXT, skip_first_screenshot=True)
        return True

    def meow_confirm(self):
        """
        Pages:
            in: MEOWFFICER_BUY
            out: page_meowfficer
        """
        # Here uses a simple click, to avoid clicking MEOWFFICER_BUY multiple times.
        # Retry logic is in meow_buy()
        self.device.click(MEOWFFICER_BUY)

        confirm_timer = Timer(1, count=2).start()
        while 1:
            self.device.screenshot()

            if self.appear_then_click(MEOWFFICER_BUY_CONFIRM, interval=5):
                continue
            if self.appear_then_click(MEOWFFICER_BUY_SKIP, interval=5):
                continue
            if self.appear(GET_ITEMS_1):
                self.device.click(MEOWFFICER_BUY_SKIP)
                continue

            # End
            if self.appear(MEOWFFICER_BUY):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        self.ui_click(MEOWFFICER_GOTO_DORM, check_button=MEOWFFICER_BUY_ENTER, appear_button=MEOWFFICER_BUY, offset=None)

    def meow_buy(self):
        """
        Pages:
            in: Any page
            out: page_main
        """
        self.ui_ensure(page_meowfficer)
        for _ in range(3):
            if self.meow_choose(count=self.config.BUY_MEOWFFICER):
                self.meow_confirm()
            else:
                self.ui_goto_main()
                return True

        logger.warning('Too many trial in meowfficer buy, stopped.')
        self.ui_goto_main()
        return False

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
