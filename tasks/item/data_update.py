from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import Digit
from tasks.base.page import page_item
from tasks.base.ui import UI
from tasks.item.assets.assets_item_data import OCR_DATA


class DataUpdate(UI):
    def _get_data(self):
        """
        Page:
            in: page_item
        """
        ocr = Digit(OCR_DATA)

        timeout = Timer(2, count=6).start()
        credit, jade = 0, 0
        while 1:
            data = ocr.detect_and_ocr(self.device.image)
            if len(data) == 2:
                credit, jade = [int(d.ocr_text) for d in data]
                if credit > 0 or jade > 0:
                    break

            logger.warning(f'Invalid credit and stellar jade: {data}')
            if timeout.reached():
                logger.warning('Get data timeout')
                break

        logger.attr('Credit', credit)
        logger.attr('StellarJade', jade)
        with self.config.multi_set():
            self.config.stored.Credit.value = credit
            self.config.stored.StallerJade.value = jade

        return credit, jade

    def run(self):
        self.ui_ensure(page_item, acquire_lang_checked=False)

        with self.config.multi_set():
            self._get_data()
            self.config.task_delay(server_update=True)
