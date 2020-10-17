from module.base.timer import Timer
from module.campaign.run import CampaignRun
from module.logger import logger
from module.ocr.ocr import Digit
from module.sos.assets import *
from module.ui.assets import CAMPAIGN_CHECK

OCR_SOS_SIGNAL = Digit(OCR_SIGNAL, letter=(255, 255, 255), threshold=128, name='OCR_SOS_SIGNAL')


class CampaignSos(CampaignRun):
    def _sos_signal_confirm(self, skip_first_screenshot=True):
        """
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
            in: Any page
            out: page_campaign
        """
        logger.hr('SOS signal search')
        self.ui_weigh_anchor()
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
