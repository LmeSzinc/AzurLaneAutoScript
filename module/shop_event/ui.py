import re

from datetime import datetime, timedelta

from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import random_rectangle_vector
from module.config.utils import server_time_offset
from module.exception import GameStuckError, ScriptError
from module.logger import logger
from module.ocr.ocr import Digit, Ocr
from module.shop.assets import SHOP_CLICK_SAFE_AREA
from module.shop.ui import ShopUI
from module.shop_event.assets import *
from module.ui.scroll import Scroll
from module.ui.ui import UI


EVENT_SHOP_SCROLL = Scroll(EVENT_SHOP_SCROLL_AREA, color=(247, 211, 66))


OCR_EVENT_SHOP_DEADLINE = Ocr(EVENT_SHOP_DEADLINE, lang='cnocr', name='OCR_EVENT_SHOP_DEADLINE', letter=(255, 247, 148), threshold=221)
OCR_EVENT_SHOP_ITEM_REMAIN = Digit(EVENT_SHOP_ITEM_REMAIN, name='OCR_EVENT_SHOP_ITEM_REMAIN', letter=(230, 227, 0), threshold=221)
OCR_EVENT_SHOP_PT_SSR = Digit(EVENT_SHOP_PT_SSR, letter=(239, 239, 239), name='OCR_EVENT_SHOP_PT')
OCR_EVENT_SHOP_PT_SSR_ENSURE = Ocr(EVENT_SHOP_PT_SSR, letter=(239, 239, 239), name='OCR_EVENT_SHOP_PT_SSR_ENSURE')
OCR_EVENT_SHOP_PT_UR = Digit(EVENT_SHOP_PT_UR, letter=(239, 239, 239), name='OCR_EVENT_SHOP_PT_UR')
OCR_EVENT_SHOP_PT_UR_ENSURE = Ocr(EVENT_SHOP_PT_UR, letter=(239, 239, 239), name='OCR_EVENT_SHOP_PT_UR_ENSURE')
OCR_EVENT_SHOP_SECOND_ENSURE = Ocr(EVENT_SHOP_SECOND_ENSURE, lang='jp', letter=(239, 239, 239), name='OCR_EVENT_SHOP_SECOND_ENSURE')

class EventShopUI(UI):
    """
    Class for Event Shop UI operations without specific item.
    """
    def event_shop_load_ensure(self, skip_first_screenshot=True):
        """
        Ensure that event shop has loaded, 
        using ocr of event pt values and pt icon at first item.
        If ocr gets nothing, then the shop is not loaded.

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: whether loaded completely
        """
        ensure_timeout = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            digits = OCR_EVENT_SHOP_PT_SSR_ENSURE.ocr(self.device.image)
            # End
            if digits != "":
                break
            else:
                logger.warning("EventShop is not fully loaded, retrying.")

            # Exception
            if ensure_timeout.reached():
                raise GameStuckError('Waiting too long for EventShop to appear.')

        ensure_timeout.reset()
        while 1:
            self.device.screenshot()

            if self.appear(EVENT_SHOP_LOAD_ENSURE):
                logger.warning("EventShop is not fully loaded, retrying.")
            else:
                break
            
            if ensure_timeout.reached():
                raise GameStuckError('Waiting too long for EventShop to appear.')

    @cached_property
    def event_shop_deadline(self):
        """
        Returns:
            datetime: server time of shop deadline.
        """
        period = OCR_EVENT_SHOP_DEADLINE.ocr(self.device.image)[:-8]
        y, m, d = [int(i) for i in re.split('[\~\-.]', period)[3:6]]
        deadline = datetime(y, m, d) + timedelta(days=1) # server deadline
        return deadline

    @cached_property
    def event_remain_days(self):
        if self.config.EVENT_SHOP_IGNORE_DEADLINE:
            return 0
        server_now = datetime.now() - server_time_offset()
        return (self.event_shop_deadline - server_now).days - 6

    @cached_property
    def event_shop_has_pt_ur(self):
        """
        Event pts are aligned as follows:
            - SSR event:    nothing,    pt
            - UR event:     pt_ur,      pt
            - assets: EVENT_SHOP_PT_UR, EVENT_SHOP_PT
        Therefore we detect pt_ur by scanning the `nothing` part.
        For SSR event Ocr() should get nothing, 
        while Digit() will always return 0.
        """
        digits = OCR_EVENT_SHOP_PT_UR_ENSURE.ocr(self.device.image)
        return digits != ""
    
    @cached_property
    def event_shop_is_commission(self):
        """
        Check if the event shop is commission shop.
        """
        return self.appear(EVENT_SHOP_COMMISSION)

    def event_shop_get_pt(self):
        """
        Event pts are aligned as follows:
            - SSR event:    nothing,    pt
            - UR event:     pt_ur,      pt
            - assets: EVENT_SHOP_PT_UR, EVENT_SHOP_PT

        Returns:
            pt (int):
        """
        amount = OCR_EVENT_SHOP_PT_SSR.ocr(self.device.image)
        logger.attr("Pt", amount)
        return amount

    def event_shop_get_pt_ur(self):
        """
        Event pts are aligned as follows:
            - SSR event:    nothing,    pt
            - UR event:     pt_ur,      pt
            - assets: EVENT_SHOP_PT_UR, EVENT_SHOP_PT

        Returns:
            pt_ur (int):

        Raises:
            ScriptError: if wrongly scans pt_ur when there isn't one.
        """
        if self.event_shop_has_pt_ur:
            amount = OCR_EVENT_SHOP_PT_UR.ocr(self.device.image)
        else:
            raise ScriptError('Should not scan UR pt at this shop')
        logger.attr("URPt", amount)
        return amount

    def init_slider(self):
        """Initialize the slider

        Returns:
            Tuple[float, float]: (pre_pos, cur_pos)
        """
        if not EVENT_SHOP_SCROLL.appear(main=self):
            logger.warning('Scroll does not appear, try to rescue slider')
            self.rescue_slider()
        retry = Timer(0, count=3)
        retry.start()
        while not EVENT_SHOP_SCROLL.at_top(main=self):
            logger.info('Scroll does not at top, try to scroll')
            EVENT_SHOP_SCROLL.set_top(main=self)
            if retry.reached():
                raise GameStuckError('Scroll drag page error.')
        return -1.0, 0.0

    def rescue_slider(self, distance=200):
        detection_area = (1130, 230, 1170, 710)
        direction_vector = (0, distance)
        p1, p2 = random_rectangle_vector(
            direction_vector, box=detection_area, random_range=(-10, -40, 10, 40), padding=10)
        self.device.drag(p1, p2, segments=2, shake=(25, 0), point_random=(0, 0, 0, 0), shake_random=(-5, 0, 5, 0))
        self.device.click(SHOP_CLICK_SAFE_AREA)
        self.device.screenshot()

    def pre_scroll(self, pre_pos, cur_pos):
        """
        Pretreatment Sliding.
        A imitation of OSShopUI.pre_scroll().

        Args:
            pre_pos: Previous position
            cur_pos: Current position

        Raise:
            ScriptError: Slide Page Error

        Returns:
            cur_pos: Current position
        """
        if pre_pos == cur_pos:
            logger.warning('Scroll drag page failed')
            if not EVENT_SHOP_SCROLL.appear(main=self):
                logger.warning('Scroll does not appear, try to rescue slider')
                self.rescue_slider()
                EVENT_SHOP_SCROLL.set(cur_pos, main=self)
            retry = Timer(0, count=3)
            retry.start()
            while 1:
                logger.warning('Scroll does not drag success, retrying scroll')
                EVENT_SHOP_SCROLL.next_page(main=self, page=0.66)
                cur_pos = EVENT_SHOP_SCROLL.cal_position(main=self)
                if pre_pos != cur_pos:
                    logger.info(f'Scroll success drag page to {cur_pos}')
                    return cur_pos
                if retry.reached():
                    raise GameStuckError('Scroll drag page error.')
        else:
            return cur_pos
