from campaign.campaign_sos.campaign_base import CampaignBase, CampaignNameError
from module.base.timer import Timer
from module.campaign.campaign_ui import STAGE_SHOWN_WAIT
from module.campaign.run import CampaignRun
from module.logger import logger
from module.ocr.ocr import Digit
from module.sos.assets import *
from module.template.assets import *
from module.ui.assets import CAMPAIGN_CHECK
from module.ui.scroll import Scroll

OCR_SOS_SIGNAL = Digit(OCR_SIGNAL, letter=(255, 255, 255), threshold=128, name='OCR_SOS_SIGNAL')
SOS_SCROLL = Scroll(SOS_SCROLL_AREA, color=(164, 173, 189), name='SOS_SCROLL')
RECORD_OPTION = ('DailyRecord', 'sos')
RECORD_SINCE = (0,)


class CampaignSos(CampaignRun, CampaignBase):

    def _find_target_chapter(self, chapter):
        """
        find the target chapter search button or goto button.

        Args:
            chapter (int): SOS target chapter
        Returns:
            Button: signal search button or goto button of the target chapter
        """
        signal_search_buttons = TEMPLATE_SIGNAL_SEARCH.match_multi(self.device.image)
        sos_goto_buttons = TEMPLATE_SIGNAL_GOTO.match_multi(self.device.image)
        all_buttons = sos_goto_buttons + signal_search_buttons
        if all_buttons is None:
            return None
        chapter_buttons = [button.crop([-403, 8, -381, 35]) for button in all_buttons]
        ocr_chapters = Digit(chapter_buttons, letter=[132, 230, 115], threshold=128, name='OCR_SOS_CHAPTER')
        chapter_list = ocr_chapters.ocr(self.device.image)
        if chapter in chapter_list:
            return all_buttons[chapter_list.index(chapter)]
        else:
            return None

    def _sos_signal_select(self, chapter, skip_first_screenshot=True):
        """
        select a SOS signal

        Pages:
            in: page_campaign
            out: page_campaign
        """
        logger.hr(f'Select chapter {chapter} signal ')
        self.ui_click(SIGNAL_SEARCH_ENTER, appear_button=CAMPAIGN_CHECK, check_button=SIGNAL_LIST_CHECK,
                      skip_first_screenshot=True)
        if chapter in [3, 4, 5]:
            positions = [0.0, 0.5, 1.0]
        elif chapter in [6, 7, 8]:
            positions = [0.5, 1.0, 0.0]
        elif chapter in [9, 10]:
            positions = [1.0, 0.5, 0.0]
        for scroll_position in positions:
            SOS_SCROLL.set(scroll_position, main=self)
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            target_button = self._find_target_chapter(chapter)
            if target_button is not None:
                self.ui_click(target_button, appear_button=SIGNAL_LIST_CHECK, check_button=CAMPAIGN_CHECK,
                              skip_first_screenshot=True)
                break

    def _sos_signal_confirm(self, skip_first_screenshot=True):
        """
        Search a SOS signal, wait for searching animation, cancel popup.

        Pages:
            in: SIGNAL_SEARCH
            out: page_campaign
        """
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(SIGNAL_SEARCHING, threshold=30):
                confirm_timer.reset()
                continue
            if self.appear_then_click(SIGNAL_SEARCH, offset=(30, 30), interval=5):
                confirm_timer.reset()
                continue
            if self.handle_popup_cancel('SIGNAL_GOTO'):
                confirm_timer.reset()
                continue

            # End
            if self.appear(CAMPAIGN_CHECK, offset=(20, 20)):
                if confirm_timer.reached():
                    return True
            else:
                confirm_timer.reset()

    def _sos_signal_search(self):
        """
        Search all SOS signals.

        Returns
            int: Signal count

        Pages:
            in: page_campaign
            out: page_campaign
        """
        logger.hr('SOS signal search')
        for n in range(12):
            self.device.screenshot()
            remain = OCR_SOS_SIGNAL.ocr(self.device.image)
            if remain > 0:
                self.ui_click(SIGNAL_SEARCH_ENTER, appear_button=CAMPAIGN_CHECK, check_button=SIGNAL_SEARCH,
                              skip_first_screenshot=True)
                self._sos_signal_confirm()
            else:
                logger.attr('SOS_signal', n)
                return n

        logger.warning('Too many SOS signals, stop searching.')
        return 8

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

    def run(self, name=None, folder='campaign_sos', total=1):
        """
        Args:
            name (str): Default to None, because stages in SOS are dynamic.
            folder (str): Default to 'campaign_sos'.
            total (int): Default to 1, because SOS stages can only run once.
        """
        logger.hr('Campaign SOS', level=1)
        self.ui_weigh_anchor()
        remain = OCR_SOS_SIGNAL.ocr(self.device.image)
        logger.attr('SOS signal', remain)
        if remain == 0:
            logger.info(f'No SOS signal, End SOS signal search')
            return True
        fleet_1 = self.config.SOS_FLEET_1
        fleet_2 = self.config.SOS_FLEET_2
        submarine = self.config.SOS_SUBMARINE
        chapter = self.config.SOS_CHAPTER
        backup = self.config.cover(FLEET_1=fleet_1, FLEET_2=fleet_2, SUBMARINE=submarine,
                                   FLEET_BOSS=1 if not fleet_2 else 2)
        while 1:
            self._sos_signal_select(chapter)
            super().run(f'campaign_{chapter}_5', folder=folder, total=total)
            remain = OCR_SOS_SIGNAL.ocr(self.device.image)
            logger.attr('remain', remain)
            if remain < 1:
                break
        backup.recover()
        logger.info(f'All SOS signals cleared')
        return True

    def record_executed_since(self):
        return self.config.record_executed_since(option=RECORD_OPTION, since=RECORD_SINCE)

    def record_save(self):
        return self.config.record_save(option=RECORD_OPTION)
