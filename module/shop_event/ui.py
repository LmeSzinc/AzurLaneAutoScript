import numpy as np
import re
from datetime import datetime, timedelta

import module.config.server as server
from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import rgb2luma, crop, color_similarity_2d
from module.config.utils import server_time_offset
from module.exception import GameStuckError
from module.logger import logger
from module.meowfficer.assets import MEOWFFICER_GET_CHECK, MEOWFFICER_TRAIN_CLICK_SAFE_AREA
from module.meowfficer.collect import SWITCH_LOCK
from module.ocr.ocr import Ocr, Digit
from module.shop.assets import SHOP_OCR_BALANCE, SHOP_OCR_OIL_CHECK, SHOP_OCR_OIL
from module.shop_event.assets import *
from module.ui.navbar import Navbar
from module.ui.scroll import Scroll
from module.ui.ui import UI


class EventShopScroll(Scroll):
    def match_color(self, main):
        delta_x = 3
        area = (self.area[0] - delta_x, self.area[1], self.area[2] + delta_x, self.area[3])
        image = main.image_crop(area, copy=False)
        image = rgb2luma(image).astype(np.float)
        dif = image[:, image.shape[1] // 2] / (image[:, 0] + image[:, -1])
        delta = np.diff(dif)
        peak_candidates = np.where(np.abs(delta) > 0.025)[0]
        if len(peak_candidates) == 2:
            assert delta[peak_candidates[0]] < 0 < delta[peak_candidates[1]]
            up, down = peak_candidates[0], peak_candidates[1]
        elif len(peak_candidates) == 1:
            if delta[peak_candidates[0]] > 0:
                up, down = 0, peak_candidates[0]
            else:
                up, down = peak_candidates[0], self.total
        else:
            logger.warning(f'peak_candidates: {peak_candidates}'
                           f'peak_values: {delta[peak_candidates]}')
            up, down = 0, 100
        mask = np.zeros((self.total,), dtype=np.bool_)
        mask[up:down] = True
        return mask


EVENT_SHOP_SCROLL = EventShopScroll(
    EVENT_SHOP_SCROLL_AREA,
    color=(0, 0, 0),
    name="EVENT_SHOP_SCROLL"
)


if server.server == 'tw':
    EVENT_SHOP_DEADLINE_COLOR = (102, 204, 255)
elif server.server == 'en':
    EVENT_SHOP_DEADLINE_COLOR = (255, 207, 129)
else:
    EVENT_SHOP_DEADLINE_COLOR = (96, 162, 62)
OCR_EVENT_SHOP_DEADLINE = Ocr(SHOP_EVENT_DEADLINE, lang='cnocr', letter=EVENT_SHOP_DEADLINE_COLOR,
                              alphabet='0123456789.:~-', name="OCR_EVENT_SHOP_DEADLINE")

if server.server == 'jp':
    OCR_EVENT_SHOP_PT = Digit(SHOP_OCR_BALANCE, lang='cnocr', letter=(110, 120, 130), name='OCR_EVENT_SHOP_PT')
    OCR_EVENT_SHOP_URPT = Digit(SHOP_OCR_BALANCE_SECOND, lang='cnocr', letter=(110, 120, 130), name='OCR_EVENT_SHOP_URPT')
else:
    OCR_EVENT_SHOP_PT = Digit(SHOP_OCR_BALANCE, letter=(100, 100, 100), name='OCR_EVENT_SHOP_PT')
    OCR_EVENT_SHOP_URPT = Digit(SHOP_OCR_BALANCE_SECOND, letter=(100, 100, 100), name='OCR_EVENT_SHOP_URPT')


class EventShopUI(UI):
    @cached_property
    def event_shop_tab_count_and_navbar(self):
        gap_x = 33
        area = (206, 92, 1092, 134)
        image = crop(self.device.image, area)
        tab = color_similarity_2d(image, color=(232, 238, 240))
        index = np.where(np.average(tab > 221, axis=0) > 0.5)[0]
        count = (area[2] - area[0] + gap_x) // (len(index) + gap_x)
        logger.info(f"Event shop tab count: {count}")
        delta_x = (area[2] - area[0] + gap_x) // count - gap_x
        grid = ButtonGrid((206, 92), (delta_x + gap_x, 44),
                          (delta_x, 44), (count, 1),
                          "EVENT_SHOP_TAB_GRID")
        navbar = Navbar(grids=grid,
                        active_color=(232, 238, 240), inactive_color=(127, 141, 151),
                        active_count=delta_x * (area[3] - area[1]) // 2,
                        inactive_count=delta_x * (area[3] - area[1]) // 2)
        return count, navbar

    @cached_property
    def event_shop_has_urpt(self):
        if self.image_color_count(SHOP_OCR_BALANCE_SECOND, OCR_EVENT_SHOP_URPT.letter, count=15):
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
        pattern = r'(\d{4})\.(\d{1,2})\.(\d{1,2})'
        matches = re.findall(pattern, period)
        if not matches or len(matches) < 2:
            logger.warning(f"Failed to read event deadline: {period}")
            return False
        y, m, d = matches[-1]
        deadline = datetime(int(y), int(m), int(d)) + timedelta(days=1)  # server deadline
        server_now = datetime.now() - server_time_offset()
        return (deadline - server_now).days < 7

    def event_shop_load_ensure(self):
        ensure_timeout = Timer(3, count=6).start()
        for _ in self.loop():
            if self.image_color_count(SHOP_OCR_BALANCE, OCR_EVENT_SHOP_PT.letter, count=15):
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

    def handle_get_meowfficer(self):
        if self.appear(MEOWFFICER_GET_CHECK, offset=(40, 40), interval=3):
            logger.info(f'Getting Meowfficer rewards.')
            SWITCH_LOCK.set('lock', main=self)
            # Wait until info bar disappears
            self.ensure_no_info_bar(timeout=1)
            self.device.click(MEOWFFICER_TRAIN_CLICK_SAFE_AREA)
            return True
        return False