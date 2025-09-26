import re
from datetime import datetime, timedelta

import module.config.server as server
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.config.utils import server_time_offset
from module.exception import GameStuckError
from module.logger import logger
from module.ocr.ocr import Ocr, Digit
from module.shop.assets import MEDAL_SHOP_SCROLL_AREA_250814, SHOP_OCR_BALANCE, SHOP_OCR_OIL_CHECK, SHOP_OCR_OIL
from module.shop.shop_medal import ShopAdaptiveScroll
from module.shop_event.assets import *
from module.ui.ui import UI


EVENT_SHOP_SCROLL = ShopAdaptiveScroll(
    MEDAL_SHOP_SCROLL_AREA_250814.button,
    background=1,
    name="EVENT_SHOP_SCROLL"
)
EVENT_SHOP_SCROLL.drag_threshold = 0.1
# A little bit larger than 0.1 to handle bottom
EVENT_SHOP_SCROLL.edge_threshold = 0.12

if server.server == 'en':
    OCR_EVENT_SHOP_DEADLINE = Ocr(SHOP_EVENT_DEADLINE, lang='cnocr', letter=(255, 207, 129),
                                  alphabet='0123456789.:~-', name="OCR_EVENT_SHOP_DEADLINE")
else:
    OCR_EVENT_SHOP_DEADLINE = Ocr(SHOP_EVENT_DEADLINE, lang='cnocr', letter=(96, 162, 62),
                                  alphabet='0123456789.:~-', name="OCR_EVENT_SHOP_DEADLINE")


class PtOcr(Digit):
    def __init__(self, buttons, lang='azur_lane', letter=(255, 255, 255), threshold=128, alphabet='0123456789IDSBL',
                 name=None):
        super().__init__(buttons, lang=lang, letter=letter, threshold=threshold, alphabet=alphabet, name=name)

    def after_process(self, result):
        result = result.replace('L', '1')
        return super().after_process(result)

if server.server == 'jp':
    OCR_EVENT_SHOP_PT = PtOcr(SHOP_OCR_BALANCE, letter=(110, 120, 130), name='OCR_EVENT_SHOP_PT')
    OCR_EVENT_SHOP_URPT = PtOcr(SHOP_OCR_BALANCE_SECOND, letter=(110, 120, 130), name='OCR_EVENT_SHOP_URPT')
else:
    OCR_EVENT_SHOP_PT = Digit(SHOP_OCR_BALANCE, letter=(100, 100, 100), name='OCR_EVENT_SHOP_PT')
    OCR_EVENT_SHOP_URPT = Digit(SHOP_OCR_BALANCE_SECOND, letter=(100, 100, 100), name='OCR_EVENT_SHOP_URPT')


class EventShopUI(UI):
    @cached_property
    def event_shop_has_urpt(self):
        if self.image_color_count(SHOP_OCR_BALANCE_SECOND, (100, 100, 100), count=15):
            logger.info("Event shop has urpt.")
            return True
        else:
            logger.info("Event shop has no urpt.")
            return False

    @cached_property
    def is_event_ended(self):
        if self.config.EVENT_SHOP_IGNORE_DEADLINE:
            return True
        period = OCR_EVENT_SHOP_DEADLINE.ocr(self.device.image)[:-8]
        y, m, d = [int(i) for i in re.split('[.~-]', period)[3:6]]
        deadline = datetime(y, m, d) + timedelta(days=1)  # server deadline
        server_now = datetime.now() - server_time_offset()
        return (deadline - server_now).days < 7

    def event_shop_load_ensure(self):
        ensure_timeout = Timer(3, count=6).start()
        for _ in self.loop():
            if self.image_color_count(SHOP_OCR_BALANCE, (100, 100, 100), count=15):
                logger.info("Event shop loaded.")
                break
            if ensure_timeout.reached():
                raise GameStuckError('Waiting too long for EventShop to appear.')
        return True

    def event_shop_get_pt(self):
        pt = OCR_EVENT_SHOP_PT.ocr(self.device.image)
        return pt

    def event_shop_get_urpt(self):
        urpt = OCR_EVENT_SHOP_URPT.ocr(self.device.image)
        return urpt

    def get_oil(self, skip_first_screenshot=True):
        """
        Returns:
            int: Oil amount
        """
        amount = 0
        timeout = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Get oil timeout')
                break

            if not self.appear(SHOP_OCR_OIL_CHECK, offset=(10, 2)):
                logger.info('No oil icon')
                continue
            ocr = Digit(SHOP_OCR_OIL, name='OCR_OIL', letter=(247, 247, 247), threshold=128)
            amount = ocr.ocr(self.device.image)
            if amount >= 100:
                break

        return amount
