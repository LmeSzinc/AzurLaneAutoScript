from campaign.campaign_sos.campaign_base import CampaignBase, CampaignNameError
from module.base.timer import Timer
from module.campaign.campaign_ui import STAGE_SHOWN_WAIT
from module.campaign.run import CampaignRun
from module.logger import logger
from module.ocr.ocr import Digit
from module.sos.assets import *
from module.ui.assets import CAMPAIGN_CHECK
from module.base.utils import *

OCR_SOS_SIGNAL = Digit(OCR_SIGNAL, letter=(255, 255, 255), threshold=128, name='OCR_SOS_SIGNAL')

sos_search_offset_dict={
    0:SIGNAL_SEARCH_LAST,
    1:SIGNAL_SEARCH_LAST_BUT_ONE,
    2:SIGNAL_SEARCH_LAST_BUT_TWO
}
sos_goto_offset_dict={
    0:SIGNAL_GOTO_LAST,
    1:SIGNAL_GOTO_LAST_BUT_ONE,
    2:SIGNAL_GOTO_LAST_BUT_TWO
}

class CampaignSos(CampaignRun, CampaignBase):
    willConsumeAllScan = False
    
    def _sos_signal_swipe(self, distance=390):
        p1, p2 = random_rectangle_vector(
            (0, -distance), box=(550, 80, 760, 470), random_range=(-10, -20, 10, 20))
        self.device.drag(p1, p2, segments=2, shake=(25, 0),
                            point_random=(0, 0, 0, 0), shake_random=(-5, 0, 5, 0))
        self.device.sleep(0.8)
        return

    def _sos_signal_confirm(self, skip_first_screenshot=True):
        """
        Search a SOS signal, wait for searching animation, cancel popup.

        Pages:
            in: SIGNAL_SEARCH
            out: page_campaign
        """
        self._sos_signal_swipe()
        self._sos_signal_swipe()
        self.device.sleep(1)
        confirm_timer = Timer(1.5, count=3).start()
        for _ in range(65):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(
                            sos_search_offset_dict.get(self.config.SOS_CHOOSE_CHAPTER_OFFSET), 
                            offset=(10, 10), interval=5):
                logger.info(f'scan offset {self.config.SOS_CHOOSE_CHAPTER_OFFSET} signal')
                confirm_timer.reset()
                continue
            if self.appear_then_click(
                            sos_goto_offset_dict.get(self.config.SOS_CHOOSE_CHAPTER_OFFSET), 
                            offset=(10, 10), interval=5):
                logger.info(f'GOTO offset {self.config.SOS_CHOOSE_CHAPTER_OFFSET} signal')
                confirm_timer.reset()
                continue
            # End
            if self.appear(CAMPAIGN_CHECK, offset=(20, 20)):
                if confirm_timer.reached():
                    return True
            else:
                confirm_timer.reset()
        logger.warning('Sos_bug_102: scan list stuck')
        logger.warning('May set wrong scan offset(optional #1)')
        return False


    def _sos_signal_search(self):
        """
        Search SOS signals once.

        Returns
            bool: =true readyed for sos battle,or =false don't battle

        Pages:
            in: page_campaign
            out: page_campaign, at where sos signal appear
        """
        logger.hr('SOS signal search')
        self.device.screenshot()
        remain = OCR_SOS_SIGNAL.ocr(self.device.image)
        logger.attr('SOS_remain', remain)
        if not remain:
            logger.info('SOS scan empty')
            return False

        if self.willConsumeAllScan or (remain >= self.config.SOS_SEARCH_STORE_UP):
            self.willConsumeAllScan = True
        else:
            logger.info('SOS store up scaning not to battle')
            return False
        self.ui_click(SIGNAL_SEARCH_ENTER, appear_button=CAMPAIGN_CHECK, check_button=SIGNAL_SEARCH_QUIT_NEW,
                        skip_first_screenshot=True)
        if not self._sos_signal_confirm():
            return False

        return True

    def _sos_signal_get(self):
        """
        Returns:
            int: Chapter index.

        Pages:
            in: page_campaign
            out: page_campaign, may in different chapter.
        """
        self.ui_click(SIGNAL_SEARCH_ENTER, appear_button=CAMPAIGN_CHECK, check_button=SIGNAL_SEARCH,
                      skip_first_screenshot=True)

        if not self.appear(SIGNAL_SEARCH_GOTO, offset=(20, 20)):
            logger.info('No SOS signal available')
            self.ui_click(SIGNAL_SEARCH_QUIT, check_button=CAMPAIGN_CHECK, skip_first_screenshot=True)
            return None

        self.ui_click(SIGNAL_SEARCH_GOTO, check_button=CAMPAIGN_CHECK, skip_first_screenshot=True)
        self.device.sleep(STAGE_SHOWN_WAIT)
        self.device.screenshot()
        chapter = self.get_chapter_index(self.device.image)
        logger.info(f'Found SOS signal in chapter {chapter}')
        return chapter

    def _sos_is_appear_at_chapter(self, chapter):
        """
        Args:
            chapter (int): 3 to 10.

        Returns:
            bool:

        Pages:
            in: page_campaign
            out: page_campaign, may in different chapter.
        """
        self.ensure_campaign_ui(name=f'{chapter}-4', mode='normal')

        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            self.device.screenshot()
            try:
                self.campaign_get_entrance('X-5')
                logger.info(f'Found SOS stage in chapter {chapter}')
                return True
            except CampaignNameError:
                if confirm_timer.reached():
                    logger.info(f'No SOS stage in chapter {chapter}')
                    return False
                else:
                    continue

    def _sos_is_appear_new(self):
        """
        detect which chapter Alas is in, and check sos signal

        Returns:
            int: =0 if no sos signal, =chapterNum if normal
        """
        logger.info('sos_in_campaign_ui')
        self.handle_stage_icon_spawn()

        confirm_timer = Timer(1.5, count=5).start()
        while 1:
            self.device.screenshot()
            try:
                self.campaign_get_entrance('X-5')
                logger.info(f'Found SOS stage')
                chapter_index_current = self.get_chapter_index(self.device.image)
                logger.info(f'SOS_using_chapter_index: {chapter_index_current}')
                return chapter_index_current
            except CampaignNameError:
                if confirm_timer.reached():
                    logger.info(f'No SOS stage')
                    return 0
                else:
                    continue

    def run(self, name=None, folder='campaign_sos', total=1):
        """
        ! out-of-date note
        Args:
            
            name (str): Default to None, because stages in SOS are dynamic.
            folder (str): Default to 'campaign_sos'.
            total (int): Default to 1, because SOS stages can only run once.
        """
        fleets = self.config.SOS_FLEETS_SET
        fleet_1 = fleets[0]
        fleet_2 = fleets[1] if len(fleets) >= 2 else 0
        submarine = fleets[2] if len(fleets) >= 3 else 0
        if not fleet_1:
            logger.info(f'Skip SOS because fleet set 0')
            return False
        self.willConsumeAllScan = False
        for _ in range(3, 11):
            self.ui_weigh_anchor()
            if not self._sos_signal_search():
                return

            chapter = self._sos_is_appear_new()
            if not chapter:
                logger.warning('Sos_unknown_bug_101')
                return
            backup = self.config.cover(FLEET_1=fleet_1, FLEET_2=fleet_2, SUBMARINE=submarine, 
                                        FLEET_BOSS=1 if not fleet_2 else 2,
                                        ENABLE_AUTO_SEARCH=False )
            super().run(f'campaign_{chapter}_5', folder=folder, total=total)
            backup.recover()

        return False
