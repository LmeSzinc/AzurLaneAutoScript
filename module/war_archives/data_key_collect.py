from module.logger import logger
from module.base.timer import Timer
from module.ocr.ocr import Digit
from module.handler.assets import GET_ITEMS_1
from module.ui.assets import CAMPAIGN_CHECK
from module.war_archives.assets import *
from module.ui.ui import UI

OCR_CURRENT_COUNT = Digit(OCR_CURRENT_DATA_KEY_COUNT, letter=(255, 247, 247), threshold=128, alphabet='0123456789')
OCR_MAX_COUNT = Digit(OCR_MAX_DATA_KEY_COUNT, letter=(255, 247, 247), threshold=128, alphabet='0123456789')
RECORD_OPTION = ('DailyRecord', 'data_key_collect')
RECORD_SINCE = (0,)

class DataKeyCollect(UI):
    def _collect_confirm(self, skip_first_screenshot=True):
        """
        Wait for results: get_items or cancel popup.

        Pages:
            in: WAR_ARCHIVES
            out: WAR_ARCHIVES
        """
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(GET_ITEMS_1, genre='get_items', offset=5):
                confirm_timer.reset()
                continue
            if self.handle_popup_cancel('DATA_KEY_LIMIT'):
                confirm_timer.reset()
                continue

            # End
            if self.appear(WAR_ARCHIVES_CHECK, offset=(20, 20)):
                if confirm_timer.reached():
                    return True
            else:
                confirm_timer.reset()

    def handle_collect(self):
        """
        Pages:
            in: page_any
            out: page_campaign
        """
        # go to page_campaign
        self.ui_weigh_anchor()

        # enter war archives
        self.ui_click(WAR_ARCHIVES_ENTER, appear_button=CAMPAIGN_CHECK, check_button=WAR_ARCHIVES_CHECK,
                      skip_first_screenshot=True)

        # if somehow already collected, then skip to exit war archives
        # else ocr check current and max data keys count, execute if current < max
        for _ in range(1):
            if self.appear(DATA_KEY_COLLECTED):
                logger.info('Shikikan has already collected today\'s data key')
                break

            current_count = OCR_CURRENT_COUNT.ocr(self.device.image)
            max_count = OCR_MAX_COUNT.ocr(self.device.image)
            logger.info(f'Data Key Status: {current_count} / {max_count}.')
            if current_count < max_count:
                self.device.click(DATA_KEY_COLLECT)
                self._collect_confirm()

        # exit war archives back into page_campaign
        self.ui_click(WAR_ARCHIVES_CHECK, appear_button=WAR_ARCHIVES_CHECK, check_button=CAMPAIGN_CHECK,
                      skip_first_screenshot=True)

    def run(self):
        """
        Returns:
            bool: If executed.
        """
        # execute collct
        self.handle_collect()

        return True

    def record_executed_since(self):
        return self.config.record_executed_since(option=RECORD_OPTION, since=RECORD_SINCE)

    def record_save(self):
        return self.config.record_save(option=RECORD_OPTION)