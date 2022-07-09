from campaign.campaign_sos.campaign_base import CampaignBase
from module.base.decorator import Config, cached_property
from module.base.utils import area_pad, random_rectangle_vector
from module.campaign.run import CampaignRun
from module.logger import logger
from module.ocr.ocr import Digit
from module.sos.assets import *
from module.template.assets import *
from module.ui.assets import CAMPAIGN_CHECK
from module.ui.page import page_campaign
from module.ui.scroll import Scroll

OCR_SOS_SIGNAL = Digit(OCR_SIGNAL, letter=(255, 255, 255), threshold=128, name='OCR_SOS_SIGNAL')


class CampaignSos(CampaignRun, CampaignBase):

    @cached_property
    @Config.when(SERVER='en')
    def _sos_chapter_crop(self):
        return [-330, 8, -285, 45]

    @cached_property
    @Config.when(SERVER='jp')
    def _sos_chapter_crop(self):
        return [-430, 8, -382, 45]

    @cached_property
    @Config.when(SERVER='tw')
    def _sos_chapter_crop(self):
        return [-400, 8, -370, 45]

    @cached_property
    @Config.when(SERVER=None)
    def _sos_chapter_crop(self):
        return [-403, 8, -381, 35]

    @cached_property
    @Config.when(SERVER='tw')
    def _sos_scroll(self):
        return Scroll(SOS_SCROLL_AREA, color=(247, 210, 66), name='SOS_SCROLL')

    @cached_property
    @Config.when(SERVER=None)
    def _sos_scroll(self):
        return Scroll(SOS_SCROLL_AREA, color=(164, 173, 189), name='SOS_SCROLL')

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
        if not len(all_buttons):
            logger.info('No SOS chapter found')
            return None

        chapter_buttons = [button.crop(self._sos_chapter_crop) for button in all_buttons]
        ocr_chapters = Digit(chapter_buttons, letter=[132, 230, 115], threshold=136, name='OCR_SOS_CHAPTER')
        chapter_list = ocr_chapters.ocr(self.device.image)
        if not isinstance(chapter_list, list):
            chapter_list = [chapter_list]
        if chapter in chapter_list:
            logger.info('Target SOS chapter found')
            return all_buttons[chapter_list.index(chapter)]
        else:
            logger.info('Target SOS chapter not found')
            return None

    @Config.when(SERVER='en')
    def _sos_signal_select(self, chapter):
        """
        select a SOS signal
        EN has no scroll bar, so the swipe signal list.

        Args:
            chapter (int): 3 to 10.

        Pages:
            in: page_campaign
            out: page_campaign, in target chapter

        Returns:
            bool: whether select successful
        """
        logger.hr(f'Select chapter {chapter} signal ')
        self.ui_click(SIGNAL_SEARCH_ENTER, appear_button=CAMPAIGN_CHECK, check_button=SIGNAL_LIST_CHECK,
                      skip_first_screenshot=True)

        detection_area = (620, 285, 720, 485)
        for _ in range(0, 5):
            target_button = self._find_target_chapter(chapter)
            if target_button is not None:
                self._sos_signal_confirm(entrance=target_button)
                return True

            # backup = self.config.cover(DEVICE_CONTROL_METHOD='minitouch')
            p1, p2 = random_rectangle_vector(
                (0, -200), box=detection_area, random_range=(-50, -50, 50, 50), padding=20)
            self.device.drag(p1, p2, segments=2, shake=(0, 25), point_random=(0, 0, 0, 0), shake_random=(0, -5, 0, 5))
            # backup.recover()
            self.device.sleep((0.6, 1))
            self.device.screenshot()
        return False

    @Config.when(SERVER=None)
    def _sos_signal_select(self, chapter):
        """
        select a SOS signal

        Args:
            chapter (int): 3 to 10.

        Pages:
            in: page_campaign
            out: page_campaign, in target chapter

        Returns:
            bool: whether select successful
        """
        logger.hr(f'Select chapter {chapter} signal ')
        self.ui_click(SIGNAL_SEARCH_ENTER, appear_button=CAMPAIGN_CHECK, check_button=SIGNAL_LIST_CHECK,
                      skip_first_screenshot=True)
        if chapter in [3, 4, 5]:
            positions = [0.0, 0.5, 1.0]
        elif chapter in [6, 7]:
            positions = [0.5, 1.0, 0.0]
        elif chapter in [8, 9, 10]:
            positions = [1.0, 0.5, 0.0]
        else:
            logger.warning(f'Unknown SOS chapter: {chapter}')
            positions = [0.0, 0.5, 1.0]

        for scroll_position in positions:
            if self._sos_scroll.appear(main=self):
                self._sos_scroll.set(scroll_position, main=self, distance_check=False)
            else:
                logger.info('SOS signal scroll not appear, skip setting scroll position')
            target_button = self._find_target_chapter(chapter)
            if target_button is not None:
                self._sos_signal_confirm(entrance=target_button)
                return True
        return False

    def _sos_signal_confirm(self, entrance, skip_first_screenshot=True):
        """
        Search a SOS signal, goto target chapter.

        Args:
            entrance (Button): Entrance button.
            skip_first_screenshot (bool):

        Pages:
            in: SIGNAL_SEARCH
            out: page_campaign
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(SIGNAL_LIST_CHECK, offset=(20, 20), interval=2):
                image = self.image_crop(area_pad(entrance.area, pad=-30))
                if TEMPLATE_SIGNAL_SEARCH.match(image):
                    self.device.click(entrance)
                if TEMPLATE_SIGNAL_GOTO.match(image):
                    self.device.click(entrance)

            # End
            if self.appear(CAMPAIGN_CHECK, offset=(20, 20)):
                break

    def run(self, name=None, folder='campaign_sos', mode='normal', total=1):
        """
        Args:
            name (str): Default to None, because stages in SOS are dynamic.
            folder (str): Default to 'campaign_sos'.
            mode (str): Must be `normal` in SOS
            total (int): Default to 1, because SOS stages can only run once.

        Pages:
            in: Any page
            out: page_campaign
        """
        logger.hr('Campaign SOS', level=1)
        self.ui_ensure(page_campaign)

        while 1:
            # End
            remain = OCR_SOS_SIGNAL.ocr(self.device.image)
            logger.attr('SOS signal', remain)
            if remain <= 0:
                logger.info(f'All SOS signals cleared')
                break

            # Run
            if self._sos_signal_select(self.config.Sos_Chapter):
                name = f'campaign_{self.config.Sos_Chapter}_5'
                self.config.override(Campaign_Name=name)
                super().run(name, folder=folder, mode=mode, total=total)
                if self.run_count > 0:
                    continue
                else:
                    self.config.task_stop()
            else:
                self.ui_click(SIGNAL_SEARCH_CLOSE, appear_button=SIGNAL_LIST_CHECK, check_button=CAMPAIGN_CHECK,
                              skip_first_screenshot=True)
                logger.warning(f'Failed to clear SOS signals, cannot locate chapter {self.config.Sos_Chapter}')
                break

        # Scheduler
        self.config.task_delay(server_update=True)
