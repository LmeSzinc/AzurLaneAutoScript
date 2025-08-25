import cv2
import numpy as np
from scipy import signal

import module.config.server as server
from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property
from module.base.timer import Timer
from module.base.utils import area_offset
from module.logger import logger
from module.base.utils import rgb2gray
from module.map_detection.utils import Points
from module.ocr.ocr import Digit, DigitYuv, Ocr
from module.shop.assets import *
from module.shop.base import ShopItemGrid, ShopItemGrid_250814
from module.shop.clerk import ShopClerk
from module.shop.shop_status import ShopStatus
from module.ui.scroll import AdaptiveScroll, Scroll

MEDAL_SHOP_SCROLL = Scroll(MEDAL_SHOP_SCROLL_AREA, color=(247, 211, 66))
MEDAL_SHOP_SCROLL.edge_threshold = 0.15
MEDAL_SHOP_SCROLL.drag_threshold = 0.15


class ShopAdaptiveScroll(AdaptiveScroll):
    def match_color(self, main):
        area = (self.area[0] - self.background, self.area[1], self.area[2] + self.background, self.area[3])
        image = main.image_crop(area, copy=False)

        image = rgb2gray(image)
        cv2.bitwise_not(image, dst=image)
        image = image.flatten()
        wlen = area[2] - area[0]
        parameters = {
            'height': (100, 200),
            'prominence': 35,
            'width': 1
        }
        parameters.update(self.parameters)
        peaks, _ = signal.find_peaks(image, **parameters)
        peaks = peaks[15: 123]
        peaks //= wlen
        self.length = 123
        mask = np.zeros((self.total,), dtype=np.bool_)
        mask[peaks] = 1
        return mask


MEDAL_SHOP_SCROLL_250814 = ShopAdaptiveScroll(
    MEDAL_SHOP_SCROLL_AREA_250814.button,
    background=1,
    name="MEDAL_SHOP_SCROLL_250814"
)
MEDAL_SHOP_SCROLL_250814.drag_threshold = 0.1
MEDAL_SHOP_SCROLL_250814.edge_threshold = 0.1


class ShopPriceOcr(DigitYuv):
    def after_process(self, result):
        result = Ocr.after_process(self, result)
        # '100' detected as '00' on retrofit blueprint
        if result == '00':
            result = '100'
        return Digit.after_process(self, result)


PRICE_OCR = ShopPriceOcr([], letter=(255, 223, 57), threshold=32, name='Price_ocr')
if server.server == 'jp':
    PRICE_OCR_250814 = Digit([], lang='cnocr', letter=(235, 235, 255), threshold=128, name='Price_ocr')
else:
    PRICE_OCR_250814 = Digit([], letter=(255, 255, 255), threshold=128, name='Price_ocr')
TEMPLATE_MEDAL_ICON = Template('./assets/shop/cost/Medal.png')
TEMPLATE_MEDAL_ICON_2 = Template('./assets/shop/cost/Medal_2.png')
TEMPLATE_MEDAL_ICON_3 = Template('./assets/shop/cost/Medal_3.png')


class MedalShop2(ShopClerk, ShopStatus):
    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return self.config.MedalShop2_Filter.strip()

    def _get_medals(self):
        """
        Returns:
            np.array: [[x1, y1], [x2, y2]], location of the medal icon upper-left corner.
        """
        area = (472, 348, 1170, 648)
        # copy image because we gonna paint it
        image = self.image_crop(area, copy=True)
        # a random background thingy that may cause mis-detection in template matching
        paint = (869, 589, 913, 643)
        paint = area_offset(paint, (-area[0], -area[1]))
        # paint it black
        x1, y1, x2, y2 = paint
        image[y1:y2, x1:x2] = (0, 0, 0)

        medals = TEMPLATE_MEDAL_ICON_2.match_multi(image, similarity=0.5, threshold=5)
        medals = Points([(0., m.area[1]) for m in medals]).group(threshold=5)
        logger.attr('Medals_icon', len(medals))
        return medals

    def wait_until_medal_appear(self, skip_first_screenshot=True):
        """
        After entering medal shop page,
        items are not loaded that fast,
        wait until any medal icon appears
        """
        timeout = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            medals = self._get_medals()

            if timeout.reached():
                break
            if len(medals):
                break

    @cached_property
    def shop_grid(self):
        return self.shop_medal_grid()

    def shop_medal_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        # (472, 348, 1170, 648)
        medals = self._get_medals()
        count = len(medals)
        if count == 0:
            logger.warning('Unable to find medal icon, assume item list is at top')
            origin_y = 246
            delta_y = 213
            row = 2
        elif count == 1:
            y_list = medals[:, 1]
            # +256, top of the crop area in _get_medals()
            # -125, from the top of medal icon to the top of shop item
            origin_y = y_list[0] + 348 - 127
            delta_y = 213
            row = 1
        elif count == 2:
            y_list = medals[:, 1]
            y1, y2 = y_list[0], y_list[1]
            origin_y = min(y1, y2) + 348 - 127
            delta_y = abs(y1 - y2)
            row = 2
        else:
            logger.warning(f'Unexpected medal icon match result: {[m for m in medals]}')
            origin_y = 246
            delta_y = 213
            row = 2

        # Make up a ButtonGrid
        # Original grid is:
        # shop_grid = ButtonGrid(
        #     origin=(476, 246), delta=(156, 213), button_shape=(98, 98), grid_shape=(5, 2), name='SHOP_GRID')
        shop_grid = ButtonGrid(
            origin=(476, origin_y), delta=(156, delta_y), button_shape=(98, 98), grid_shape=(5, row), name='SHOP_GRID')
        return shop_grid

    shop_template_folder = './assets/shop/medal'

    @cached_property
    def shop_medal_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_medal_items = ShopItemGrid(
            shop_grid,
            templates={}, amount_area=(60, 74, 96, 95),
            price_area=(52, 132, 132, 162))
        shop_medal_items.load_template_folder(self.shop_template_folder)
        shop_medal_items.load_cost_template_folder('./assets/shop/cost')
        shop_medal_items.similarity = 0.85  # Lower the threshold for consistent matches of PR/DRBP
        shop_medal_items.cost_similarity = 0.5
        shop_medal_items.price_ocr = PRICE_OCR
        return shop_medal_items

    def shop_items(self):
        """
        Shared alias name for all shops,
        so to use  @Config must define
        a unique alias as cover

        Returns:
            ShopItemGrid:
        """
        return self.shop_medal_items

    def shop_currency(self):
        """
        Ocr shop medal currency
        Then return medal count

        Returns:
            int: medal amount
        """
        self._currency = self.status_get_medal()
        logger.info(f'Medal: {self._currency}')
        return self._currency

    def shop_has_loaded(self, items):
        """
        If any item parsed with a default
        price of 5000; then shop cannot
        be safely bought from yet

        Returns:
            bool
        """
        for item in items:
            if int(item.price) == 5000:
                return False
        return True

    def shop_interval_clear(self):
        """
        Clear interval on select assets for
        shop_buy_handle
        """
        super().shop_interval_clear()
        self.interval_clear(SHOP_BUY_CONFIRM_SELECT)
        self.interval_clear(SHOP_BUY_CONFIRM_AMOUNT)

    def shop_buy_handle(self, item):
        """
        Handle shop_medal buy interface if detected

        Args:
            item: Item to handle

        Returns:
            bool: whether interface was detected and handled
        """
        if self.appear(SHOP_BUY_CONFIRM_SELECT, offset=(20, 20), interval=3):
            self.shop_buy_select_execute(item)
            self.interval_reset(SHOP_BUY_CONFIRM_SELECT)
            return True
        if self.appear(SHOP_BUY_CONFIRM_AMOUNT, offset=(20, 20), interval=3):
            self.shop_buy_amount_execute(item)
            self.interval_reset(SHOP_BUY_CONFIRM_AMOUNT)
            return True

        return False

    def run(self):
        """
        Run Medal Shop
        """
        # Base case; exit run if filter empty
        if not self.shop_filter:
            return

        # When called, expected to be in
        # correct Medal Shop interface
        logger.hr('Medal Shop', level=1)
        self.wait_until_medal_appear()

        # Execute buy operations
        MEDAL_SHOP_SCROLL.set_top(main=self)
        while 1:
            self.shop_buy()
            if MEDAL_SHOP_SCROLL.at_bottom(main=self):
                logger.info('Medal shop reach bottom, stop')
                break
            else:
                MEDAL_SHOP_SCROLL.next_page(main=self, page=0.66)
                del_cached_property(self, 'shop_grid')
                del_cached_property(self, 'shop_medal_items')
                continue


class MedalShop2_250814(MedalShop2):
    # New UI in 2025-08-14
    def _get_medals(self):
        """
        Returns:
            np.array: [[x1, y1], [x2, y2]], location of the medal icon upper-left corner.
        """
        area = (226, 317, 960, 635)
        # copy image because we gonna paint it
        image = self.image_crop(area, copy=True)
        medals = TEMPLATE_MEDAL_ICON_3.match_multi(image, similarity=0.5, threshold=5)
        medals = Points([(0., m.area[1]) for m in medals]).group(threshold=5)
        logger.attr('Medals_icon', len(medals))
        return medals

    def shop_medal_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        # (472, 348, 1170, 648)
        medals = self._get_medals()
        count = len(medals)
        if count == 0:
            logger.warning('Unable to find medal icon, assume item list is at top')
            origin_y = 228
            delta_y = 217
            row = 2
        elif count == 1:
            y_list = medals[:, 1]
            # +256, top of the crop area in _get_medals()
            # -125, from the top of medal icon to the top of shop item
            origin_y = y_list[0] + 317 - 126
            delta_y = 217
            row = 1
        elif count == 2:
            y_list = medals[:, 1]
            y1, y2 = y_list[0], y_list[1]
            origin_y = min(y1, y2) + 317 - 126
            delta_y = abs(y1 - y2)
            row = 2
        else:
            logger.warning(f'Unexpected medal icon match result: {[m for m in medals]}')
            origin_y = 228
            delta_y = 217
            row = 2

        # Make up a ButtonGrid
        # Original grid is:
        # shop_grid = ButtonGrid(
        #     origin=(476, 246), delta=(156, 213), button_shape=(98, 98), grid_shape=(5, 2), name='SHOP_GRID')
        shop_grid = ButtonGrid(
            origin=(226, origin_y), delta=(162, delta_y), button_shape=(64, 64), grid_shape=(5, row), name='SHOP_GRID')
        return shop_grid

    @cached_property
    def shop_medal_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_medal_items = ShopItemGrid_250814(
            shop_grid,
            templates={}, amount_area=(60, 74, 96, 95),
            price_area=(14, 122, 85, 149), cost_area=(-12, 115, 60, 155))
        shop_medal_items.load_template_folder(self.shop_template_folder)
        shop_medal_items.load_cost_template_folder('./assets/shop/cost')
        shop_medal_items.similarity = 0.85  # Lower the threshold for consistent matches of PR/DRBP
        shop_medal_items.cost_similarity = 0.5
        shop_medal_items.price_ocr = PRICE_OCR_250814
        return shop_medal_items

    def run(self):
        """
        Run Medal Shop
        """
        # Base case; exit run if filter empty
        import time
        if not self.shop_filter:
            return

        # When called, expected to be in
        # correct Medal Shop interface
        logger.hr('Medal Shop', level=1)
        # Execute buy operations
        MEDAL_SHOP_SCROLL_250814.set_top(main=self)
        time.sleep(0.5)
        while 1:
            self.shop_buy()
            if MEDAL_SHOP_SCROLL_250814.at_bottom(main=self):
                logger.info('Medal shop reach bottom, stop')
                break
            else:
                MEDAL_SHOP_SCROLL_250814.next_page(main=self, page=0.66)
                del_cached_property(self, 'shop_grid')
                del_cached_property(self, 'shop_medal_items')
                continue
