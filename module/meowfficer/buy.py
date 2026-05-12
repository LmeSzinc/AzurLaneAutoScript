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
    def meow_get_buy_count(self) -> int:
        """
        OCR remaining buys and coins, combine with user configs to decide
        how many meowfficer boxes to buy this run.

        Baseline: buy up to Meowfficer_BuyAmount per day.
        Overflow: when Meowfficer_OverflowCoins is not -1 and current coins
        exceed it, keep buying extra boxes until coins drop to threshold or
        today's quota runs out. The 1st box per day is free.

        Pages:
            in: page_meowfficer

        Returns:
            int: 0 to BUY_MAX, number of boxes to buy now.
        """
        self.device.screenshot()
        remain, bought, total = MEOWFFICER.ocr(self.device.image)
        coins = MEOWFFICER_COINS.ocr(self.device.image)
        logger.attr('Meowfficer_remain', remain)
        logger.attr('Meowfficer_coins', coins)

        if total != BUY_MAX:
            logger.warning(f'Invalid meowfficer buy limit: {total}, revise to {BUY_MAX}')
            total = BUY_MAX
            bought = total - remain

        today_left = max(0, total - bought)
        if today_left <= 0:
            logger.info(f'Already bought {bought}/{total} today, stopped')
            return 0

        # Baseline buy
        baseline = min(max(0, self.config.Meowfficer_BuyAmount - bought), today_left)

        # Overflow buy
        overflow_th = self.config.Meowfficer_OverflowCoins
        extra = 0
        if overflow_th != -1 and coins > overflow_th:
            extra = -(-(coins - overflow_th) // BUY_PRIZE)
            extra = min(extra, today_left - baseline)
            extra = max(0, extra)

        count = baseline + extra

        # Cap by affordable coins, the 1st box per day is free
        free = 1 if bought == 0 else 0
        affordable = coins // BUY_PRIZE + free
        if count > affordable:
            logger.info(f'Current coins only afford to buy {affordable}')
            count = affordable

        logger.info(
            f'Meowfficer buy plan: count={count}, baseline={baseline}, '
            f'overflow={extra}, bought={bought}/{total}, coins={coins}'
        )
        return count

    def meow_choose(self, count) -> None:
        """
        Navigate to MEOWFFICER_BUY and set buy index to `count`.

        Pages:
            in: page_meowfficer
            out: MEOWFFICER_BUY

        Args:
            count (int): 1 to BUY_MAX.
        """
        self.meow_enter(MEOWFFICER_BUY_ENTER, check_button=MEOWFFICER_BUY)
        self.ui_ensure_index(count, letter=MEOWFFICER_CHOOSE, prev_button=MEOWFFICER_BUY_PREV,
                             next_button=MEOWFFICER_BUY_NEXT, skip_first_screenshot=True)

    def meow_confirm(self, skip_first_screenshot=True) -> None:
        """
        Pages:
            in: MEOWFFICER_BUY
            out: page_meowfficer
        """
        # Here uses a simple click, to avoid clicking MEOWFFICER_BUY multiple times.
        logger.hr('Meow confirm')
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
                # Rare case that MEOWFFICER_INFO popups here
                if self.meow_additional():
                    continue

                # End
                if self.match_template_color(MEOWFFICER_BUY_ENTER, offset=(20, 20)):
                    break

    def meow_buy(self) -> None:
        """
        Buy meowfficer boxes according to baseline and optional overflow plan.

        Pages:
            in: page_meowfficer
            out: page_meowfficer
        """
        logger.hr('Meowfficer buy', level=1)
        count = self.meow_get_buy_count()
        if count <= 0:
            return
        self.meow_choose(count)
        self.meow_confirm()
