from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1
from module.config.utils import get_server_next_update
from module.handler.assets import INFO_BAR_1
from module.logger import logger
from module.meowfficer.assets import *
from module.ocr.ocr import Digit, DigitCounter
from module.ui.assets import MEOWFFICER_GOTO_DORM, MEOWFFICER_INFO
from module.ui.ui import UI, page_meowfficer

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

        self.ui_click(MEOWFFICER_BUY_ENTER, check_button=MEOWFFICER_BUY,
                      additional=self.meow_additional, retry_wait=3, skip_first_screenshot=True)
        self.ui_ensure_index(count, letter=MEOWFFICER_CHOOSE, prev_button=MEOWFFICER_BUY_PREV,
                             next_button=MEOWFFICER_BUY_NEXT, skip_first_screenshot=True)
        return True

    def meow_additional(self):
        if self.appear_then_click(MEOWFFICER_INFO, offset=(30, 30), interval=3):
            return True

        return False

    def handle_meow_popup_confirm(self):
        if self.appear_then_click(MEOWFFICER_CONFIRM, offset=(40, 20), interval=5):
            return True
        else:
            return False

    def meow_confirm(self, skip_first_screenshot=True):
        """
        Pages:
            in: MEOWFFICER_BUY
            out: page_meowfficer
        """
        # Here uses a simple click, to avoid clicking MEOWFFICER_BUY multiple times.
        # Retry logic is in meow_buy()
        executed = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(MEOWFFICER_BUY, offset=(20, 20), interval=3):
                if executed:
                    self.device.click(MEOWFFICER_GOTO_DORM)
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
                self.device.click(MEOWFFICER_BUY_SKIP)
                self.interval_clear(MEOWFFICER_BUY)
                executed = True
                continue

            # End
            if self.appear(MEOWFFICER_BUY_ENTER, offset=(20, 20)) \
                    and MEOWFFICER_BUY_ENTER.match_appear_on(self.device.image):
                break

    def meow_get(self, skip_first_screenshot=True):
        """
        Transition through all the necessary screens
        to acquire each trained meowfficer
        Animation is waited for as the amount can vary
        Only SR will prompt MEOWFFICER_LOCK_CONFIRM

        Args:
            skip_first_screenshot (bool): Skip first
            screen shot or not

        Pages:
            in: MEOWFFICER_STATUS
            out: MEOWFFICER_TRAIN
        """
        # Used to account for the cat box opening animation
        self.wait_until_appear(MEOWFFICER_STATUS, offset=(40, 40))

        # Loop through possible screen transitions
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_meow_popup_confirm():
                confirm_timer.reset()
                continue
            if self.appear(MEOWFFICER_STATUS, offset=(40, 40), interval=3):
                self.device.multi_click(MEOWFFICER_TRAIN_CLICK_SAFE_AREA, 2)
                confirm_timer.reset()
                continue

            # End
            if self.appear(MEOWFFICER_TRAIN_START, offset=(20, 20)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def meow_queue(self):
        """
        Queue all remaining empty slots to begin
        meowfficer training
        Begin with single click then loop check
        screen transitions

        Pages:
            in: MEOWFFICER_TRAIN
            out: MEOWFFICER_TRAIN
        """
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
                self.device.sleep(0.3)
                self.device.click(MEOWFFICER_TRAIN_START)
                confirm_timer.reset()
                continue
            if self.handle_meow_popup_confirm():
                confirm_timer.reset()
                continue

            # End
            if self.appear(MEOWFFICER_TRAIN_START, offset=(20, 20)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def meow_buy(self):
        """
        Pages:
            in: page_meowfficer
            out: page_meowfficer
        """
        for _ in range(3):
            if self.meow_choose(count=self.config.Meowfficer_BuyAmount):
                self.meow_confirm()
            else:
                return True

        logger.warning('Too many trial in meowfficer buy, stopped.')
        return False

    def meow_collect(self, is_sunday=False):
        """
        Collect one or all trained meowfficer(s)
        Completed slots are automatically moved
        to top of queue, assume to check top-left
        slot only

        Args:
            is_sunday (bool): Whether today is Sunday or not

        Pages:
            in: MEOWFFICER_TRAIN
            out: MEOWFFICER_TRAIN

        Returns:
            Bool whether collected or not
        """
        if self.appear(MEOWFFICER_TRAIN_COMPLETE, offset=(20, 20)):
            # Today is Sunday, finish all else get just one
            if is_sunday:
                self.device.click(MEOWFFICER_TRAIN_FINISH_ALL)
            else:
                self.device.click(MEOWFFICER_TRAIN_COMPLETE)

            # Get loop mechanism to collect all trained meowfficer
            self.meow_get()
            return True
        return False

    def meow_train(self):
        """
        Performs both retrieving a trained meowfficer and queuing
        meowfficer boxes for training

        Pages:
            in: page_meowfficer
            out: page_meowfficer
        """
        # Retrieve capacity to determine whether able to collect
        current, remain, total = MEOWFFICER_CAPACITY.ocr(self.device.image)
        logger.attr('Meowfficer_capacity_remain', remain)

        # Helper variables
        is_sunday = get_server_next_update(self.config.Scheduler_ServerUpdate).weekday() == 0
        collected = False

        # Enter MEOWFFICER_TRAIN window
        self.ui_click(MEOWFFICER_TRAIN_ENTER, check_button=MEOWFFICER_TRAIN_START,
                      additional=self.meow_additional, retry_wait=3, skip_first_screenshot=True)

        # If today is Sunday, then collect all remainder otherwise just collect one
        # Once collected, should be back in MEOWFFICER_TRAIN window
        if remain > 0:
            collected = self.meow_collect(is_sunday)

        # FIll queue to full if
        # - Attempted to collect but failed,
        #   indicating in progress or completely
        #   empty
        # - Today is Sunday
        # Once queued, should be back in MEOWFFICER_TRAIN window
        if (remain > 0 and not collected) or is_sunday:
            self.meow_queue()

        self.ui_click(MEOWFFICER_GOTO_DORM,
                      check_button=MEOWFFICER_TRAIN_ENTER, appear_button=MEOWFFICER_TRAIN_START, offset=None)

        return collected

    def meow_chores(self, skip_first_screenshot=True):
        """
        Loop through all chore mechanics to
        get fort xp points

        Args:
            skip_first_screenshot (bool): Skip first
            screen shot or not

        Pages:
            in: MEOWFFICER_FORT
            out: MEOWFFICER_FORT
        """
        self.interval_clear(GET_ITEMS_1)
        check_timer = Timer(1, count=2)
        confirm_timer = Timer(1.5, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(MEOWFFICER_FORT_GET_XP_1) or \
                    self.appear(MEOWFFICER_FORT_GET_XP_2):
                check_timer.reset()
                confirm_timer.reset()
                continue

            if self.appear(GET_ITEMS_1, offset=5, interval=3):
                self.device.click(MEOWFFICER_FORT_CHECK)
                check_timer.reset()
                confirm_timer.reset()
                continue

            if check_timer.reached():
                is_chore = self.image_color_count(
                    MEOWFFICER_FORT_CHORE, color=(247, 186, 90),
                    threshold=235, count=50)
                check_timer.reset()
                if is_chore:
                    self.device.click(MEOWFFICER_FORT_CHORE)
                    confirm_timer.reset()
                    continue

            # End
            if self.appear(MEOWFFICER_FORT_CHECK, offset=(20, 20)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def meow_fort(self):
        """
        Performs fort chores if available,
        applies to every meowfficer simultaneously

        Pages:
            in: page_meowfficer
            out: page_meowfficer
        """
        # Check for fort red notification
        if not self.appear(MEOWFFICER_FORT_RED_DOT):
            return False

        # Enter MEOWFFICER_FORT window
        self.ui_click(MEOWFFICER_FORT_ENTER, check_button=MEOWFFICER_FORT_CHECK,
                      additional=self.meow_additional, retry_wait=3, skip_first_screenshot=True)

        # Perform fort chore operations
        self.meow_chores()

        # Exit back into page_meowfficer
        def additional():
            if self.appear_then_click(GET_ITEMS_1, offset=5, interval=3):
                return True
            return False

        self.ui_click(MEOWFFICER_GOTO_DORM,
                      check_button=MEOWFFICER_FORT_ENTER, appear_button=MEOWFFICER_FORT_CHECK,
                      additional=additional, offset=None, skip_first_screenshot=True)

        return True

    def run(self):
        """
        Execute buy, train, and fort operations
        if enabled by arguments

        Pages:
            in: Any page
            out: page_meowfficer
        """
        if self.config.Meowfficer_BuyAmount <= 0 \
                and not self.config.Meowfficer_TrainMeowfficer \
                and not self.config.Meowfficer_FortChoreMeowfficer:
            self.config.Scheduler_Enable = False
            self.config.task_stop()

        self.ui_ensure(page_meowfficer)

        if self.config.Meowfficer_BuyAmount > 0:
            self.meow_buy()
        if self.config.Meowfficer_TrainMeowfficer:
            self.meow_train()
        if self.config.Meowfficer_FortChoreMeowfficer:
            self.meow_fort()

        self.config.task_delay(server_update=True)
