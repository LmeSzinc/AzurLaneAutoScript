from module.base.button import ButtonGrid
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

MEOWFFICER_SELECT_GRID = ButtonGrid(
    origin=(770, 245), delta=(130, 147), button_shape=(70, 20), grid_shape=(4, 3),
    name='MEOWFFICER_SELECT_GRID')
MEOWFFICER_FEED_GRID = ButtonGrid(
    origin=(818, 212), delta=(130, 147), button_shape=(30, 30), grid_shape=(4, 3),
    name='MEOWFFICER_FEED_GRID')
MEOWFFICER_FEED = DigitCounter(OCR_MEOWFFICER_FEED, letter=(131, 121, 123), threshold=64)

MEOWFFICER_QUEUE = DigitCounter(OCR_MEOWFFICER_QUEUE, letter=(131, 121, 123), threshold=64)
MEOWFFICER_BOX_GRID = ButtonGrid(
    origin=(460, 210), delta=(160, 0), button_shape=(30, 30), grid_shape=(3, 1),
    name='MEOWFFICER_BOX_GRID')
MEOWFFICER_BOX_COUNT_GRID = ButtonGrid(
    origin=(776, 21), delta=(133, 0), button_shape=(65, 27), grid_shape=(3, 1),
    name='MEOWFFICER_BOX_COUNT_GRID')
MEOWFFICER_BOX_COUNT = Digit(MEOWFFICER_BOX_COUNT_GRID.buttons,
    letter=(16, 12, 0), threshold=64,
    name='MEOWFFICER_BOX_COUNT')


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

    def meow_feed_scan(self):
        """
        Scan for meowfficers that can be fed
        into target meowfficer for enhancement

        Pages:
            in: MEOWFFICER_FEED
            out: MEOWFFICER_FEED

        Returns:
            list(Button)
        """
        clickable = []
        for index, button in enumerate(MEOWFFICER_FEED_GRID.buttons):
            # Exit if 11th button; no need to validate as not
            # possible to click beyond this point
            if index >= 10:
                break

            # Exit if button is empty slot
            if self.image_color_count(button, color=(231, 223, 221), threshold=221, count=450):
                break

            # Continue onto next if button
            # already selected (green check mark)
            if self.image_color_count(button, color=(95, 229, 108), threshold=221, count=150):
                continue

            # Neither base case, so presume
            # button is clickable
            clickable.append(button)

        return clickable

    def meow_feed_select(self):
        """
        Click and confirm the meowfficers that
        can be used as feed to enhance the target
        meowfficer

        Pages:
            in: MEOWFFICER_FEED
            out: MEOWFFICER_ENHANCE
        """
        current = 0
        while 1:
            # Scan for feed, exit if none
            buttons = self.meow_feed_scan()
            if not len(buttons):
                break

            # Else click each button to
            # apply green check mark
            # Sleep for stable image
            for button in buttons:
                self.device.click(button)
            self.device.sleep((0.3, 0.5))
            self.device.screenshot()

            # Exit if maximum clicked
            current, remain, total = MEOWFFICER_FEED.ocr(self.device.image)
            if not remain:
                break

        # Use current to pass appropriate button for ui_click
        # route back to MEOWFFICER_ENHANCE
        self.ui_click(MEOWFFICER_FEED_CONFIRM if current else MEOWFFICER_FEED_CANCEL,
                      check_button=MEOWFFICER_ENHANCE_CONFIRM, offset=(20, 20))

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

    def _meow_queue_enter(self, skip_first_screenshot=True):
        """
        Transition into the queuing window to
        enqueue meowfficer boxes
        May fail to enter so limit to 3 tries
        before giving up

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool, whether able to enter into
            MEOWFFICER_TRAIN_FILL_QUEUE
        """
        timeout_count = 3
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

                if not self.appear(MEOWFFICER_TRAIN_FILL_QUEUE, offset=(20, 20)) \
                    and self.appear(MEOWFFICER_TRAIN_START, offset=(20, 20), interval=3):
                    if timeout_count > 0:
                        self.device.click(MEOWFFICER_TRAIN_START)
                        timeout_count -= 1
                    else:
                        return False

                if self.appear(MEOWFFICER_TRAIN_FILL_QUEUE, offset=(20, 20)):
                    return True

    def _meow_nqueue(self, skip_first_screenshot=True):
        """
        Queue all remaining empty slots does
        so autonomously enqueuing rare boxes
        first

        Pages:
            in: MEOWFFICER_TRAIN
            out: MEOWFFICER_TRAIN
        """
        # Loop through possible screen transitions
        # as a result of the previous action
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
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

    def _meow_rqueue(self):
        """
        Queue all remaining empty slots however does
        so manually in order to enqueue common
        boxes first

        Pages:
            in: MEOWFFICER_TRAIN
            out: MEOWFFICER_TRAIN
        """
        counts = MEOWFFICER_BOX_COUNT.ocr(self.device.image)
        buttons = MEOWFFICER_BOX_GRID.buttons
        while 1:
            # Number that can be queued
            current, remain, total = MEOWFFICER_QUEUE.ocr(self.device.image)
            if not remain:
                break

            # Loop as needed to queue boxes appropriately
            for i, j in ((0, 2), (1, 1)):
                count = counts[i] - remain
                if count < 0:
                    self.device.multi_click(buttons[j], remain + count)
                    remain = abs(count)
                else:
                    self.device.multi_click(buttons[j], remain)
                    break

            self.device.sleep((0.3, 0.5))
            self.device.screenshot()

        # Re-use mechanism to transition through screens
        self._meow_nqueue()

    def meow_queue(self):
        """
        Enter into training window and then
        choose appropriate queue method based
        on current stock

        Pages:
            in: MEOWFFICER_TRAIN
            out: MEOWFFICER_TRAIN
        """
        # Either can remain in same window or
        # enter the queuing window
        if not self._meow_queue_enter():
            return

        # Get count; read from meowfficer root page
        # Cannot reliably read from queuing page
        counts = MEOWFFICER_BOX_COUNT.ocr(self.device.image)
        common_sum = counts[0] + counts[1]

        # Choose appropriate queue func based on
        # common box sum count
        # - <= 20, low stock; set Meowfficer_EnhanceIndex
        #   to 0 (turn off) and queue normally
        # - > 20, high stock; queue common boxes first
        if not self.config.Meowfficer_EnhanceIndex or common_sum <= 20:
            if self.config.Meowfficer_EnhanceIndex:
                self.config.Meowfficer_EnhanceIndex = 0
                self.config.modified['Meowfficer.Meowfficer.EnhanceIndex'] = 0
                self.config.save()
            self._meow_nqueue()
        else:
            self._meow_rqueue()


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

    def _meow_select(self, skip_first_screenshot=True):
        """
        Select the target meowfficer in the
        MEOWFFICER_SELECT/FEED_GRID (4x3)
        Ensure through dotted yellow/white
        circle appearance after click

        Args:
            skip_first_screenshot (bool):
        """
        # Calculate (x, y) coordinate within
        # MEOWFFICER_SELECT/FEED_GRID (4x3) for
        # enhance target
        index = self.config.Meowfficer_EnhanceIndex - 1
        x = index if index < 4 else index % 4
        y = index // 4

        # Must confirm selected
        # Dotted yellow/white circle
        # around target meowfficer
        click_timer = Timer(3, count=6)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.meow_additional():
                click_timer.reset()
                continue

            if self.image_color_count(MEOWFFICER_SELECT_GRID[x, y], color=(255, 255, 255), threshold=246, count=100):
                break

            if click_timer.reached():
                self.device.click(MEOWFFICER_FEED_GRID[x, y])
                click_timer.reset()

    def meow_enhance_confirm(self, skip_first_screenshot=True):
        """
        Finalize feed materials for enhancement
        of meowfficer
        Pages:
            in: MEOWFFICER_ENHANCE
            out: MEOWFFICER_ENHANCE
        """
        confirm_timer = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(MEOWFFICER_FEED_ENTER, offset=(20, 20)):
                if confirm_timer.reached():
                    break
                continue

            if self.handle_meow_popup_confirm():
                confirm_timer.reset()
                continue
            if self.appear_then_click(MEOWFFICER_ENHANCE_CONFIRM, offset=(20, 20), interval=3):
                confirm_timer.reset()
                continue

    def meow_enhance(self):
        """
        Perform meowfficer enhancement operations
        involving using extraneous meowfficers to
        donate XP into a meowfficer target

        Pages:
            in: page_meowfficer
            out: page_meowfficer
        """
        # Base Cases
        # - Config at least > 0
        # - Coins at least > 1000
        if self.config.Meowfficer_EnhanceIndex <= 0:
            return

        coins = MEOWFFICER_COINS.ocr(self.device.image)
        if coins < 1000:
            return

        # Select target meowfficer
        # for enhancement
        self._meow_select()

        # Transition to MEOWFFICER_FEED after
        # selection; broken up due to significant
        # delayed behavior of meow_additional
        self.ui_click(MEOWFFICER_ENHANCE_ENTER, check_button=MEOWFFICER_FEED_ENTER,
                      additional=self.meow_additional, retry_wait=3, skip_first_screenshot=True)
        self.ui_click(MEOWFFICER_FEED_ENTER, check_button=MEOWFFICER_FEED_CONFIRM,
                      additional=self.meow_additional, retry_wait=3, skip_first_screenshot=True)

        # Initiate feed sequence
        # - Select Feed
        # - Confirm/Cancel Feed
        # - Confirm Enhancement
        self.meow_feed_select()
        self.meow_enhance_confirm()

        # Exit back into page_meowfficer
        self.ui_click(MEOWFFICER_GOTO_DORM, check_button=MEOWFFICER_ENHANCE_ENTER,
                      appear_button=MEOWFFICER_ENHANCE_CONFIRM, offset=None)

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
        is_sunday = True
        if not self.config.Meowfficer_EnhanceIndex:
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

        self.ui_click(MEOWFFICER_GOTO_DORM, check_button=MEOWFFICER_TRAIN_ENTER,
                      appear_button=MEOWFFICER_TRAIN_START, offset=None)

        # Clear meowfficer space for upcoming week iff not configured
        # for enhancement and is_sunday
        if is_sunday and not self.config.Meowfficer_EnhanceIndex:
            backup = self.config.temporary(Meowfficer_EnhanceIndex=1)
            self.meow_enhance()
            backup.recover()

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
        if self.config.Meowfficer_EnhanceIndex > 0:
            self.meow_enhance()
        if self.config.Meowfficer_TrainMeowfficer:
            self.meow_train()
        if self.config.Meowfficer_FortChoreMeowfficer:
            self.meow_fort()

        self.config.task_delay(server_update=True)
