from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from module.reward.assets import *
from module.handler.assets import INFO_BAR_1
from module.ui.ui import UI, page_meowfficer, MEOWFFICER_GOTO_DORM

BUY_MAX = 15
BUY_PRIZE = 1500
MEOWFFICER = DigitCounter(OCR_MEOWFFICER, letter=(140, 113, 99), threshold=64)
MEOWFFICER_CHOOSE = Digit(OCR_MEOWFFICER_CHOOSE, letter=(140, 113, 99), threshold=64)
MEOWFFICER_COINS = Digit(OCR_MEOWFFICER_COINS, letter=(99, 69, 41), threshold=64)
MEOWFFICER_CAPACITY = DigitCounter(OCR_MEOWFFICER_CAPACITY, letter=(131, 121, 123), threshold=64)


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

    def meow_check(self, isSunday):
        """
        Pages:
            in: page_meowfficer
            out: True: MEOWFFICER_STATUS or False: page_meowfficer

        Args:
            isSunday (bool): Determine type of collection is used.

        Returns:
            bool: True if able to collect, False otherwise.
        """
        current, remain, total = MEOWFFICER_CAPACITY.ocr(self.device.image)
        logger.attr('Meowfficer_remain', remain)

        # Check capacity status, 0 implies no space left
        if remain > 0:
            self.ui_click(MEOWFFICER_TRAIN_ENTER,
                          check_button=MEOWFFICER_TRAIN_START, skip_first_screenshot=True)

            # At least one completed, completed slots are automatically moved to top-left
            # Else go back to page_meowfficer
            if self.appear(MEOWFFICIER_TRAIN_COMPLETE, offset=(20, 20)):
                # Today is Sunday, finish all else get just one
                if isSunday:
                    self.device.click(MEOWFFICER_TRAIN_FINISH_ALL)
                else:
                    self.device.click(MEOWFFICIER_TRAIN_COMPLETE)
                return True
            else:
                self.ui_click(MEOWFFICER_GOTO_DORM,
                              check_button=MEOWFFICER_TRAIN_ENTER, appear_button=MEOWFFICER_TRAIN_START, offset=None)

        return False

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

        self.ui_click(MEOWFFICER_GOTO_DORM,
                      check_button=MEOWFFICER_BUY_ENTER, appear_button=MEOWFFICER_BUY, offset=None)

    def meow_get(self, skip_first_screenshot=True):
        """
        Pages:
            in: MEOWFFICER_STATUS
            out: page_meowfficer
        """

        # Used to account for the cat box opening animation
        self.wait_until_appear(MEOWFFICER_STATUS)

        # Loop through possible screen transitions
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(MEOWFFICER_STATUS, interval=3):
                confirm_timer.reset()
                continue
            if self.appear_then_click(MEOWFFICER_LOCK_CONFIRM, offset=(20, 20), interval=3):
                confirm_timer.reset()
                continue

            # End
            if self.appear(MEOWFFICER_TRAIN_START, offset=(20, 20)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        self.ui_click(MEOWFFICER_GOTO_DORM,
                      check_button=MEOWFFICER_TRAIN_ENTER, appear_button=MEOWFFICER_TRAIN_START, offset=None)

    def meow_train(self):
        """
        Pages:
            in: page_meowfficer
            out: page_meowfficer
        """

        # Transition to correct pages/windows
        self.ui_click(MEOWFFICER_TRAIN_ENTER,
                      check_button=MEOWFFICER_TRAIN_START, skip_first_screenshot=True)

        # Try to start a training session
        self.device.click(MEOWFFICER_TRAIN_START)

        # Loop through possible screen transitions
        # as a result of the previous action
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            self.device.screenshot()

            if self.appear(INFO_BAR_1):
                confirm_timer.reset()
                continue
            if self.appear_then_click(MEOWFFICER_TRAIN_FILL_QUEUE, offset=(20, 20), interval=5):
                self.device.click(MEOWFFICER_TRAIN_START)
                confirm_timer.reset()
                continue
            if self.appear_then_click(MEOWFFICER_TRAIN_CONFIRM, offset=(20, 20), interval=5):
                confirm_timer.reset()
                continue

            # End
            if self.appear(MEOWFFICER_TRAIN_START, offset=(20, 20)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        # May click multiple depending on current screenshot
        self.ui_click(MEOWFFICER_GOTO_DORM,
                      check_button=MEOWFFICER_TRAIN_ENTER, appear_button=MEOWFFICER_TRAIN_START, offset=None)

    def meow_buy(self):
        """
        Pages:
            in: page_meowfficer
            out: page_meowfficer
        """
        for _ in range(3):
            if self.meow_choose(count=self.config.BUY_MEOWFFICER):
                self.meow_confirm()
            else:
                return True

        logger.warning('Too many trial in meowfficer buy, stopped.')
        return False

    def meow_collect(self):
        """
        Pages:
            in: page_meowfficer
            out: page_meowfficer
        """
        # Determine if final day, used for two separate actions
        isSunday = self.config.get_server_last_update((0,)).weekday() == 6
        if self.meow_check(isSunday):
            self.meow_get()

        # Final day, fill train queue for next week i.e. tomorrow
        if isSunday:
            self.meow_train()

    def meow_run(self, buy=True, collect=True):
        """
        Pages:
            in: Any page
            out: page_main
        """
        if not buy and not collect:
            return False

        self.ui_ensure(page_meowfficer)

        if buy:
            self.meow_buy()

        if collect:
            self.meow_collect()

        self.ui_goto_main()
        return True

    def handle_meowfficer(self):
        """
        Returns:
            bool: If executed
        """
        if self.config.record_executed_since(option=('RewardRecord', 'meowfficer'), since=(0,)):
            return False

        if not self.meow_run(buy=self.config.BUY_MEOWFFICER >= 1, collect=True):
            return False

        self.config.record_save(option=('RewardRecord', 'meowfficer'))
        return True
