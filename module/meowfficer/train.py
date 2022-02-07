from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.config.utils import get_server_next_update
from module.handler.assets import INFO_BAR_1
from module.logger import logger
from module.meowfficer.assets import *
from module.meowfficer.collect import MeowfficerCollect
from module.meowfficer.enhance import MeowfficerEnhance
from module.ocr.ocr import Digit, DigitCounter
from module.ui.assets import MEOWFFICER_GOTO_DORM

MEOWFFICER_CAPACITY = DigitCounter(OCR_MEOWFFICER_CAPACITY, letter=(131, 121, 123), threshold=64)
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


class MeowfficerTrain(MeowfficerCollect, MeowfficerEnhance):
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
