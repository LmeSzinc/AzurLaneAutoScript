from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1
from module.config.utils import get_server_next_update
from module.handler.assets import INFO_BAR_1
from module.logger import logger
from module.meowfficer.assets import *
from module.ocr.ocr import *
from module.ui.assets import MEOWFFICER_GOTO_DORM, MEOWFFICER_INFO
from module.ui.ui import UI, page_meowfficer
from module.ui.scroll import Scroll
from scipy import signal

BUY_MAX = 15
BUY_PRIZE = 1500
MEOWFFICER = DigitCounter(OCR_MEOWFFICER, letter=(140, 113, 99), threshold=64)
MEOWFFICER_CHOOSE = Digit(OCR_MEOWFFICER_CHOOSE, letter=(140, 113, 99), threshold=64)
MEOWFFICER_COINS = Digit(OCR_MEOWFFICER_COINS, letter=(99, 69, 41), threshold=64)
MEOWFFICER_CAPACITY = DigitCounter(OCR_MEOWFFICER_CAPACITY, letter=(131, 121, 123), threshold=64)
MEOWFFICER_SCROLL = Scroll(MEOWFFICER_SCROLL_AREA, color=(255, 219, 99), name='MEOWFFICER_SCROLL')

SCREENERDICT_CAMP = {
    'USS': 0,
    'HMS': 1,
    'INR': 2,
    'KMS': 3,
    'ROC': 4,
    'SN': 5,
    'FFNF': 6,
    'MNF': 7
}

SCREENERDICT_RARITY = {
    'SuperRare': 0,
    'Rare': 1,
    'Normal': 2
}

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
        elif self.appear_then_click(MEOWFFICER_FEED_SELECT_SSR_COFIRM, offset=(30, 30), interval=3):
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
        self.interval_reset(MEOWFFICER_CONFIRM)
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
            if self.appear(MEOWFFICER_TRAIN_START, offset=(20, 20)) and \
                MEOWFFICER_TRAIN_START.match_appear_on(self.device.image):
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

    def meow_train(self, is_sunday):
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
        collected = False
        boxCount = 0

        # Check the boxes in the warehouse to determin whether able to train
        boxButtonList = ButtonGrid(origin=(774, 20), delta=(133, 0), 
                                          button_shape=(72, 27), grid_shape=(3, 1)).buttons            
        boxCountList = Ocr(buttons=boxButtonList, name='Box Count', letter=(99, 69, 41), 
                                  threshold = 64, alphabet='0123456789').ocr(image=self.device.image)
        for i in range(3):
            boxCount += int(boxCountList[i])

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
            if boxCount > 0:
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
        check_timer = Timer(1, count=2)
        confirm_timer = Timer(1.5, count=3).start()
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

            if self.appear(GET_ITEMS_1, interval=5):
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
        self.ui_click(MEOWFFICER_GOTO_DORM,
                      check_button=MEOWFFICER_FORT_ENTER, appear_button=MEOWFFICER_FORT_CHECK, offset=None)

        return True

    def meow_screened(self):
        """
        Change the screener of meowfficer

        Pages:
            in: page_meowfficer
            out: page_meowfficer
        
        Returns: 
            bool: if screener changed

        """
        logger.hr('Change screener', level=2)
        screened =  False

        if not self.appear(MEOWFFICER_SCREENER_ENTER):
            logger.warning('Can not find screener')
            return screened

        # Enter screener page
        self.ui_click(click_button=MEOWFFICER_SCREENER_ENTER, check_button=MEOWFFICER_SCREENER_START, offset=0, retry_wait=3, skip_first_screenshot=True)
        campButtons = ButtonGrid(origin=(398, 355), delta=(124, 42),button_shape=(91, 28), grid_shape=(4, 2)).buttons
        rarityButtons = ButtonGrid(origin=(522, 493), delta=(124, 0), button_shape=(91, 28), grid_shape=(3, 1)).buttons

        # Reset screener
        self.ui_click(click_button=MEOWFFICER_SCREENER_CAMP_CHANGED, check_button=MEOWFFICER_SCREENER_CAMP_DEFAULT, offset=0, skip_first_screenshot=True)
        self.ui_click(click_button=MEOWFFICER_SCREENER_RARITY_CHANGED, check_button=MEOWFFICER_SCREENER_RARITY_DEFAULT, offset=0, skip_first_screenshot=True)

        # Changer screener
        logger.attr('Meowfficer Camp', self.config.Meowfficer_ScreenerCamp)
        logger.attr('Meowfficer Rarity', self.config.Meowfficer_ScreenerRarity)
        if self.config.Meowfficer_ScreenerCamp != 'default':
            self.ui_click(click_button=campButtons[SCREENERDICT_CAMP[self.config.Meowfficer_ScreenerCamp]],
                          appear_button=MEOWFFICER_SCREENER_CAMP_DEFAULT,
                          check_button=MEOWFFICER_SCREENER_CAMP_CHANGED, 
                          offset=0, skip_first_screenshot=True)
            screened = True
        if self.config.Meowfficer_ScreenerRarity != 'default':
            self.ui_click(click_button=rarityButtons[SCREENERDICT_RARITY[self.config.Meowfficer_ScreenerRarity]],
                          appear_button=MEOWFFICER_SCREENER_RARITY_DEFAULT,
                          check_button=MEOWFFICER_SCREENER_RARITY_CHANGED, 
                          offset=0, skip_first_screenshot=True)
            screened = True

        # Out of screener page
        self.ui_click(click_button=MEOWFFICER_SCREENER_CONFIRM, check_button=MEOWFFICER_FORT_ENTER, offset=0, skip_first_screenshot=True)
        return screened

    def meow_select(self, min_level = 1, max_level = 30):
        """
        Select the meowfficer(s) by level between
        min_level and max_level

        Pages:
            in: page_meowfficer
            out: page_meowfficer
            OR 
            in: MEOWFFICER_FEED
            out: MEOWFFICER_FEED

        Returns:
            List: List of the meowfficer(ButtonGrid)
        """
        logger.hr('Get meowfficer list in current page', level=2)
        self.device.screenshot()
        targetMeowfficerList = []

        # Get meowfficer level button list and level ocr
        meowfficerButtonList = ButtonGrid(origin=(760, 221), delta=(130, 147), 
                                          button_shape=(18, 18), grid_shape=(4, 3)).buttons        
        meowfficerLevelList = Ocr(buttons=meowfficerButtonList, name='Meowfficer Level List', letter=(49, 48, 49), 
                                  threshold = 64, alphabet='0123456789').ocr(image=self.device.image)

        # Reset wrong level
        meowfficerLevelList = [x if (x == '' or (int(x) > 0 and int(x) <= 30))
                               else str(30) if int(x) == 0 
                               else str(int(x) - 50) if int(x) >= 70
                               else x
                               for x in meowfficerLevelList] 
        logger.attr("Final meowfficer list:", meowfficerLevelList)

        targetMeowfficerList = [x for (x, y) in zip(meowfficerButtonList, meowfficerLevelList) 
                                  if y != '' and int(y) >= min_level and int(y) <= max_level]        
        return targetMeowfficerList

    def meow_feed_enter(self, meowfficerList=[], skip_first_screenshot=True):
        """
        Find the first meowfficer not in combat and feed it

        Pages:
            in: page_meowfficer
            out: page_meowfficer

        Args: 
            list of meowfficers

        Return:
            bool: whether feeted at least one time or not
        """
        feeded = False
        choosed = False

        # index of meowfficer
        i = 0
        while 1:   
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            
            # Enter the target meowfficer feeding page
            if self.appear(MEOWFFICER_FEED_SELECT_ENTER):
                feeded = self.meow_feed_target()
                break

            # Check the index of meowfficerList
            if len(meowfficerList) <= i:
                logger.info('Can\'t find meowfficer to feed in Final meowfficer list')
                return feeded

            # Buttom INFO_BAR_1 means that the choosed meowfficer is in combat
            if self.appear(INFO_BAR_1):
                logger.info('Choosed meowfficer is in combat')
                choosed = False
                i += 1
                self.wait_until_disappear(INFO_BAR_1)
                continue
            else:
                # Choose the target meowfficer
                if not choosed and self.meow_ensure_choosed_meowfficer(meowfficerList[i]):
                    choosed = True
                if self.appear(MEOWFFICER_FEED_ENTER):
                    self.device.click(MEOWFFICER_FEED_ENTER)
                    self.device.sleep(0.3)
                    continue

        # Out of MEOWFFICER_FEED window
        self.ui_click(MEOWFFICER_GOTO_DORM, check_button=MEOWFFICER_FEED_ENTER, offset=None)
        return feeded  

    def meow_ensure_choosed_meowfficer(self, btnMeowfficer, skip_first_screenshot=True):
        """
        Try to choose the target meoffcier

        Args:
            btnMeofficer: button of the target meofficer

        Return:
            bool: True if target meowfficer is choosed
        """
        while(1):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # If a meowfficer is choosed, confirmPoints(RGB=255, 227, 132) will appear in button area
            confirmPoints = color_similarity_2d(self.device.image.crop(btnMeowfficer.area), (255, 227, 132))
            confirmPoints = [i for j in confirmPoints for i in j]
            peaks, _ = signal.find_peaks(confirmPoints, height=230)
            if len(peaks) != 0:
                logger.info('Target meowfficer is choosed')
                logger.attr('peaks', peaks)
                break
            else:
                logger.info('Target meowfficer is not choosed')
                self.device.click(btnMeowfficer)
                self.device.sleep(0.3)
        return True

    def meow_feed_consumed(self):
        """
        Consume meowfficer in the warehouse

        Pages:
            in: MEOWFFICER_FEED_SELECT window
            out: MEOWFFICER_FEED window

        Returns:
            bool: still have meofficer to consumed or not
        """
        # Select items with values within the max_level and mini_level values
        targetMeowfficerList = self.meow_select(min_level=1, max_level=1)

        # Check list
        if len(targetMeowfficerList) == 0:
                logger.info('Not enough meowfficers to consumed, stopped')
                self.ui_click(MEOWFFICER_FEED_SELECT_CANCEL, check_button=MEOWFFICER_FEED_SELECT_ENTER,
                              additional=self.meow_additional, retry_wait=3, skip_first_screenshot=True)
                return False

        # Select the meowfficer(s) that will be consumed
        for i in range(10 if 10 < len(targetMeowfficerList) else len(targetMeowfficerList)):
            self.device.click(targetMeowfficerList[i])
            self.device.sleep(0.2)

        # Out of MEOWFFICER_FEED_SELECT window
        self.ui_click(MEOWFFICER_FEED_SELECT_CONFIRM, check_button=MEOWFFICER_FEED_CONFIRM,
                      additional=self.meow_additional, retry_wait=3, skip_first_screenshot=True)
        return True

    def meow_feed_target(self):
        """
        Feed target meowfficer

        Pages:
            in: MEOWFFICER_FEED window
            out: MEOWFFICER_FEED window

        Returns:
            bool: whether feeted at least one time or not
        """    
        feeded = False
        while 1:
            self.device.screenshot()

            # Enter MEOWFFICER_FEED_SELECT window
            if self.appear(MEOWFFICER_FEED_SELECT_ENTER):
                self.ui_click(MEOWFFICER_FEED_SELECT_ENTER, check_button=MEOWFFICER_FEED_SELECT_CANCEL,
                              additional=self.meow_additional, retry_wait=3, skip_first_screenshot=True)
                consumed = self.meow_feed_consumed()
                if not consumed:
                    break

            # Click confirm
            if self.appear(MEOWFFICER_FEED_CONFIRM):
                self.ui_click(MEOWFFICER_FEED_CONFIRM, check_button=MEOWFFICER_FEED_SELECT_ENTER, 
                              additional=self.meow_additional, retry_wait=3, skip_first_screenshot=True)
                feeded = True

            # Check current page and the Level of the meowfficer
            if 30 == Ocr(buttons=(788, 334, 828, 363), name='Meowfficer level', 
                         letter=(255, 255, 255), threshold=96).ocr(self.device.image):
                logger.info('Choosed meofficer level is 30')
                break
        
        return feeded

    def meow_feed(self):
        """
        Feed meowfficer

        Pages:
            in: page_meowfficer
            out: page_meowfficer

        Returns:
            bool whether feeted at least once or not
        """
        logger.hr('Feed Meowfficer', level=1)
        self.ui_ensure(page_meowfficer)
        feeded = False

        # Change screener
        self.meow_screened()

        # Get meowfficer list in the first page
        meowfficerList = self.meow_select(min_level=self.config.Meowfficer_MeofficerMinLevel, 
                                          max_level=self.config.Meowfficer_MeofficerMaxLevel)

        # try to enter the feed page
        if len(meowfficerList) > 0:         
            feeded = self.meow_feed_enter(meowfficerList, skip_first_screenshot=True)
        else:
            logger.info('Can not find any meowfficer')

        if feeded:
            logger.info('Feed success')
        else:
            logger.info('Feed failed')
        return feeded

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
        is_sunday = get_server_next_update(self.config.Scheduler_ServerUpdate).weekday() == 0

        if self.config.Meowfficer_BuyAmount > 0:
            self.meow_buy()
        if self.config.Meowfficer_FortChoreMeowfficer:
            self.meow_fort()
        if not self.config.Meowfficer_FeedMeowfficer and self.config.Meowfficer_TrainMeowfficer:
            self.meow_train(is_sunday)
        if not self.config.Meowfficer_FeedMeowfficer:
            self.config.task_delay(server_update=True)

        if self.config.Meowfficer_FeedMeowfficer:
            self.meow_train(is_sunday=True)
            self.meow_feed()
            self.config.task_delay(server_update=True, minute=180)

