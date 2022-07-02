import inflection

from module.combat.assets import GET_ITEMS_1
from module.logger import logger
from module.meowfficer.assets import *
from module.meowfficer.base import MeowfficerBase
from module.ocr.ocr import Digit, DigitCounter
from module.ui.assets import MEOWFFICER_GOTO_DORMMENU

BUY_MAX = 15
BUY_PRIZE = 1500
MEOWFFICER = DigitCounter(OCR_MEOWFFICER, letter=(140, 113, 99), threshold=64)
MEOWFFICER_CHOOSE = Digit(OCR_MEOWFFICER_CHOOSE, letter=(140, 113, 99), threshold=64)
MEOWFFICER_COINS = Digit(OCR_MEOWFFICER_COINS, letter=(99, 69, 41), threshold=64)


class MeowfficerBuy(MeowfficerBase):
    def meow_choose(self, count) -> bool:
        """
        Pages:
            in: page_meowfficer
            out: MEOWFFICER_BUY

        Args:
            count (int): 0 to 15.

        Returns:
            bool: If success.
        """
        remain, bought, total = MEOWFFICER.ocr(self.device.image)
        logger.attr('Meowfficer_remain', remain)

        # Check buy status
        if total != BUY_MAX:
            logger.warning(f'Invalid meowfficer buy limit: {total}, revise to {BUY_MAX}')
            total = BUY_MAX
            bought = total - remain
        if bought > 0:
            if bought >= count:
                logger.info(f'Already bought {bought} today, stopped')
                return False
            else:
                count -= bought
                logger.info(f'Already bought {bought} today, only need to buy {count} more')

        # Check coins
        coins = MEOWFFICER_COINS.ocr(self.device.image)
        if (coins < BUY_PRIZE) and (remain < total):
            logger.info('Not enough coins to buy one, stopped')
            return False
        elif (count - int(remain == total)) * BUY_PRIZE > coins:
            count = coins // BUY_PRIZE + int(remain == total)
            logger.info(f'Current coins only enough to buy {count}')

        self.ui_click(MEOWFFICER_BUY_ENTER, check_button=MEOWFFICER_BUY, additional=self.meow_additional,
                      retry_wait=3, confirm_wait=0, skip_first_screenshot=True)
        self.ui_ensure_index(count, letter=MEOWFFICER_CHOOSE, prev_button=MEOWFFICER_BUY_PREV,
                             next_button=MEOWFFICER_BUY_NEXT, skip_first_screenshot=True)
        return True

    def meow_confirm(self, skip_first_screenshot=True) -> None:
        """
        Pages:
            in: MEOWFFICER_BUY
            out: page_meowfficer
        """
        # Here uses a simple click, to avoid clicking MEOWFFICER_BUY multiple times.
        # Retry logic is in meow_buy()
        executed = False
        with self.stat.new(
                genre="meowfficer_buy",
                method=self.config.DropRecord_MeowfficerBuy,
        ) as drop:
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                if self.appear(MEOWFFICER_BUY, offset=(20, 20), interval=3):
                    if executed:
                        self.device.click(MEOWFFICER_GOTO_DORMMENU)
                    else:
                        self.device.click(MEOWFFICER_BUY)
                    continue
                if self.handle_meow_popup_confirm():
                    executed = True
                    continue
                if self.appear_then_click(MEOWFFICER_BUY_SKIP, interval=3):
                    executed = True
                    continue
                if self.appear(GET_ITEMS_1, offset=5, interval=3):
                    if drop.save is True:
                        drop.handle_add(self, before=2)
                    self.device.click(MEOWFFICER_BUY_SKIP)
                    self.interval_clear(MEOWFFICER_BUY)
                    executed = True
                    continue

                # End
                if self.appear(MEOWFFICER_BUY_ENTER, offset=(20, 20)) \
                        and MEOWFFICER_BUY_ENTER.match_appear_on(self.device.image):
                    break

    def meow_buy(self) -> bool:
        """
        Pages:
            in: page_meowfficer
            out: page_meowfficer
        """
        logger.hr('Meowfficer buy', level=1)

        for _ in range(3):
            if self.meow_choose(count=self.config.Meowfficer_BuyAmount):
                self.meow_confirm()
            else:
                return True

        logger.warning('Too many trial in meowfficer buy, stopped.')
        return False
