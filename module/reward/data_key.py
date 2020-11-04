from module.logger import logger
from module.base.timer import Timer
from module.ocr.ocr import DigitCounter
from module.handler.assets import GET_ITEMS_1
from module.ui.assets import WAR_ARCHIVES_CHECK
from module.reward.assets import OCR_DATA_KEY, DATA_KEY_COLLECT, DATA_KEY_COLLECTED
from module.ui.ui import UI, page_archives

DATA_KEY = DigitCounter(OCR_DATA_KEY, letter=(255, 247, 247), threshold=64)
RECORD_OPTION = ('RewardRecord', 'data_key')
RECORD_SINCE = (0,)

class RewardDataKey(UI):
    def _data_key_collect_confirm(self, skip_first_screenshot=True):
        """
        Wait for results: get_items or cancel popup.

        Pages:
            in: page_archives
            out: page_archives
        """
        result = True
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
                    return result
            else:
                confirm_timer.reset()

    def data_key_collect(self):
        """
        Execute data key collection

        Pages:
            in: page_any
            out: page_main
        """
        self.ui_ensure(page_archives)

        for n in range(3):
            if self.appear(DATA_KEY_COLLECTED):
                logger.info('Data key has been collected')
                return True

            current, remain, total = DATA_KEY.ocr(self.device.image)
            logger.info(f'Inventory: {current} / {total}, Remain: {remain}')
            if remain <= 0:
                if n == 2:
                    logger.warn('No more room for additional data key')
                continue

            self.device.click(DATA_KEY_COLLECT)
            self._data_key_collect_confirm()
            continue

        logger.warn('Too many tries on data key collection, skip and try again on next reward loop')
        self.ui_goto_main()
        return False

    def handle_data_key(self):
        if not self.config.ENABLE_DATA_KEY_COLLECT:
            return False

        if self.record_executed_since():
            return False

        if not self.data_key_collect():
            return False

        self.record_save()
        return True

    def record_executed_since(self):
        return self.config.record_executed_since(option=RECORD_OPTION, since=RECORD_SINCE)

    def record_save(self):
        return self.config.record_save(option=RECORD_OPTION)