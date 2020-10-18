from module.base.timer import Timer
from module.campaign.campaign_ui import CampaignUI, STAGE_SHOWN_WAIT
from module.campaign.run import CampaignRun
from module.logger import logger
from module.ocr.ocr import Digit
from module.sos.assets import *
from module.ui.assets import CAMPAIGN_CHECK

OCR_SOS_SIGNAL = Digit(OCR_SIGNAL, letter=(255, 255, 255), threshold=128, name='OCR_SOS_SIGNAL')


class CampaignSos(CampaignRun, CampaignUI):
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
            str: Name of map files to run, such as 'campaign_3_5'

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
        return f'campaign_{chapter}_5'

    def run(self, name=None, folder='campaign_sos', total=1):
        """
        Args:
            name (str): Default to None, because stages in SOS are dynamic.
            folder (str): Default to 'campaign_sos'.
            total (int): Default to 1, because SOS stages can only run once.
        """
        self.ui_weigh_anchor()
        self._sos_signal_search()

        for _ in range(10):
            name = self._sos_signal_get()
            if not name:
                return True

            super().run(name, folder=folder, total=total)

        logger.warning('Too many available SOS signals, stop running.')
        return False
