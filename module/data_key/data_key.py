from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1
from module.logger import logger
from module.ocr.ocr import DigitCounter
from module.data_key.assets import OCR_DATA_KEY, DATA_KEY_COLLECT, DATA_KEY_COLLECTED
from module.ui.assets import WAR_ARCHIVES_CHECK
from module.ui.ui import UI, page_archives
from module.war_archives.assets import WAR_ARCHIVES_EX_ON

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
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GET_ITEMS_1, offset=5, interval=3):
                # Clicking any blank area in page_archives will exit to page_campaign.
                # Click WAR_ARCHIVES_EX to avoid this, if double clicking GET_ITEMS.
                self.device.click(WAR_ARCHIVES_EX_ON)
                confirm_timer.reset()
                continue
            if self.handle_popup_confirm('DATA_KEY_LIMIT'):
                # If it's in 29/30 means user is not doing war achieves frequently,
                # no need to bother losing one key, just make it full filled.
                confirm_timer.reset()
                continue

            # End
            if self.appear(WAR_ARCHIVES_CHECK, offset=(20, 20)):
                if confirm_timer.reached():
                    return True
            else:
                confirm_timer.reset()

    def data_key_collect(self):
        """
        Execute data key collection

        Returns:
            bool: If success to run.

        Pages:
            in: page_any
            out: page_main
        """
        self.ui_ensure(page_archives)

        for n in range(3):
            self.device.screenshot()
            if self.appear(DATA_KEY_COLLECTED):
                logger.info('Data key has been collected')
                self.ui_goto_main()
                return True

            current, remain, total = DATA_KEY.ocr(self.device.image)
            logger.info(f'Inventory: {current} / {total}, Remain: {remain}')
            if remain <= 0:
                logger.info('No more room for additional data key')
                self.ui_goto_main()
                return True

            self.device.click(DATA_KEY_COLLECT)
            self._data_key_collect_confirm()
            continue

        logger.warning('Too many tries on data key collection, skip and try again on next task run')
        self.ui_goto_main()
        return False

    def run(self):
        """
        Handle data_key operations if configured to do so.

        Pages:
            in: page_any
            out: page_main
        """
        if not self.data_key_collect():
            self.config.task_delay(success=False)
        else:
            self.config.task_delay(server_update=True)
