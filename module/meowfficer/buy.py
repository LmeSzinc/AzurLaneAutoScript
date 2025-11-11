from module.combat.assets import GET_ITEMS_1
from module.logger import logger
from module.meowfficer.assets import *
from module.meowfficer.base import MeowfficerBase
from module.ocr.ocr import Digit, DigitCounter
from module.ui.assets import MEOWFFICER_GOTO_DORMMENU
import math

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

        self.meow_enter(MEOWFFICER_BUY_ENTER, check_button=MEOWFFICER_BUY)
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

    def meow_buy(self) -> bool:
        """Buy Meowfficers by baseline plan and optional overflow plan.

        Pages:
            in: page_meowfficer
            out: page_meowfficer

        Returns:
        bool: Always True (no blocking errors).
        """
        logger.hr('Meowfficer buy', level=1)

        def _read():
            """Screenshot + OCR once; normalize total to BUY_MAX if needed."""
            self.device.screenshot()
            remain, bought, total = MEOWFFICER.ocr(self.device.image)
            coins = MEOWFFICER_COINS.ocr(self.device.image)
            if total != BUY_MAX:
                logger.warning(f'Invalid meowfficer buy limit: {total}, revise to {BUY_MAX}')
                total = BUY_MAX
                bought = total - remain
            return remain, bought, total, coins

        def _attempt(target_total_today: int) -> bool:
            """Try choose+confirm up to 3 times; target means today's total bought."""
            for _ in range(3):
                if self.meow_choose(count=target_total_today):
                    self.meow_confirm()
                    return True
                return False
            return False

        remain, bought, total, coins = _read()

        desired = int(getattr(self.config, 'Meowfficer_BuyAmount', 0))
        overflow_th = getattr(self.config, 'Meowfficer_OverflowCoins', None)
        try:
            overflow_th = int(overflow_th) if overflow_th is not None else None
        except Exception:
            overflow_th = None  # Disable overflow if invalid.

        today_left = max(0, total - int(bought))

        baseline = max(0, min(desired, today_left, BUY_MAX))
        if baseline > 0:
            logger.info(
                f'[Meowfficer] baseline buy={baseline} | coins={coins} | '
                f'desired={desired} | bought_today={bought}/{total}'
            )
            target_total_today = min(total, int(bought) + baseline)
            if _attempt(target_total_today):
                remain, bought, total, coins = _read() 

        if overflow_th is None:
            return True

        if coins > overflow_th:
            need_more = math.ceil((coins - overflow_th) / BUY_PRIZE)  
            today_left = max(0, total - int(bought))                  
            planned = max(1, min(need_more, today_left, BUY_MAX))   
            if planned <= 0:
                logger.info('No extra to buy after overflow planning.')
                return True

            target_total_today = min(total, int(bought) + planned)
            logger.info(
                f'[Meowfficer] overflow extra buy={planned} | coins={coins} | overflow_th={overflow_th} | '
                f'bought_today={bought}/{total} -> target_total_today={target_total_today}'
            )
            _attempt(target_total_today)

        return True

