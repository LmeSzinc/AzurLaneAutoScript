# import cv2
# import numpy as np

from module.base.utils import *

from typing import List

from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property
from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import Ocr, DigitYuv
from module.map_detection.utils import Points
from module.shop.assets import *
from module.shop.base import ShopItemGrid
from module.shop.clerk import ShopClerk
from module.shop.shop_medal import MEDAL_SHOP_SCROLL
from module.shop.shop_status import ShopStatus
from module.shop.ui import ShopUI
from module.statistics.item import Item


class CounterOcr(Ocr):
    def __init__(self, buttons, lang='azur_lane', letter=(255, 255, 255), threshold=128, alphabet='0123456789/IDSB@OQZl',
                 name=None):
        super().__init__(buttons, lang=lang, letter=letter, threshold=threshold, alphabet=alphabet, name=name)

    def pre_process(self, image):
        image = rgb2gray(image)
        return image

    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('I', '1').replace('D', '0').replace('S', '5')
        result = result.replace('B', '8').replace('Z', '2').replace('l', '1')
        result = result.replace('@', '0').replace('O', '0').replace('Q', '0')
        return result

    def ocr(self, image, direct_ocr=False):
        """
        Do OCR on a counter, such as `14/15`, and returns 14, 15

        Args:
            image:
            direct_ocr:

        Returns:
            list[list[int]: [[current, total]].
        """
        result_list = super().ocr(image, direct_ocr=direct_ocr)
        if isinstance(result_list, list):
            return [[int(j) for j in i.split('/')]for i in result_list]
        else:
            return [int(i) for i in result_list.split('/')]

COUNTER_OCR = CounterOcr([], lang='cnocr', name='Counter_ocr')
PRICE_OCR = DigitYuv([], letter=(255, 223, 57), threshold=32, name='Price_ocr')


class EventShopItem(Item):
    # mainly used to distinguish equip skin box and event equip
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_count = 1
        self.count = 1

    def __str__(self):
        if self.name != 'DefaultItem' and self.cost == 'DefaultCost':
            name = f'{self.name}_x{self.amount}'
        elif self.name == 'DefaultItem' and self.cost != 'DefaultCost':
            name = f'{self.cost}_x{self.price}'
        elif self.name.isdigit():
            name = f'{self.name}_{self.count}/{self.total_count}_{self.cost}_x{self.price}'
        else:
            name = f'{self.name}_x{self.amount}_{self.cost}_x{self.price}'

        if self.tag is not None:
            name = f'{name}_{self.tag}'

        return name


class EventShopItemGrid(ShopItemGrid):
    item_class = EventShopItem
    pt_icon = None

    def __init__(self, grids, templates, template_area=(40, 21, 89, 70), amount_area=(60, 71, 91, 92),
                 cost_area=(6, 123, 84, 176), price_area=(52, 132, 132, 156), tag_area=(81, 4, 91, 8),
                 counter_area=(80, 170, 138, 190)):
        super().__init__(grids, templates, template_area, amount_area, cost_area, price_area, tag_area)
        self.counter_ocr = COUNTER_OCR
        self.counter_area = counter_area

    def match_cost_template(self, item):
        """
        Overwrite ItemGrid.match_cost_template.

        Returns:
            str: Template name = 'pt'.
        """
        image = item.crop(self.cost_area)
        res = cv2.matchTemplate(image, np.array(self.pt_icon), cv2.TM_CCOEFF_NORMED)
        _, similarity, _, _ = cv2.minMaxLoc(res)
        if similarity > self.cost_similarity:
            return "pt"
        
        return None

    def predict(self, image, name=True, amount=True, cost=True, price=True, tag=False, counter=True) -> List[EventShopItem]:
        """
        Args:
            image (np.ndarray):
            counter (bool): If predict item counter.
            shop_index (bool): If predict shop index.
            scroll_pos (bool): If predict scroll position.

        Returns:
            list[Item]:
        """
        super().predict(image, name, amount=True, cost=cost, price=price, tag=tag)
        # temporary code to distinguish between DR and PR. Shit code.
        for item in self.items:
            if item.name.startswith('DR') and item.price == 500:
                item.name = 'P' + item.name[1:]
            if item.name.startswith('PR') and item.price == 1000:
                item.name = 'D' + item.name[1:]

        if counter and len(self.items):
            counter_list = [item.crop(self.counter_area) for item in self.items]
            counter_list = self.counter_ocr.ocr(counter_list, direct_ocr=True)
            for i, t in zip(self.items, counter_list):
                i.count, i.total_count = t

        return self.items

class EventShop(ShopClerk, ShopUI, ShopStatus):
    shop_template_folder = './assets/shop/event'
    pt_icon = None

    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return self.config.EventShop_Filter.strip()

    def record_pt_icon(self):
        """
        Record event pt icon for medal-shop-like itemgrid detection.
        Call this method before doing swipes in event shop page.
        """
        logger.info('RECORD EVENT PT ICON')
        # self.device.screenshot()

        self.pt_icon = self.image_crop((489, 372, 525, 408), copy=False)

    def _get_pt_icons(self):
        """
        Returns:
            np.array: [[x1, y1], [x2, y2]], location of the medal icon upper-left corner.
        """
        left_column = self.image_crop((472, 348, 1170, 625), copy=False)
        res = cv2.matchTemplate(left_column, np.array(
            self.pt_icon), cv2.TM_CCOEFF_NORMED)

        icons = np.array(np.where(res >= 0.4)).T[:, ::-1]
        icons = Points([(0., i[1]) for i in icons]).group(threshold=5)
        logger.attr('PT_icon', len(icons))
        return icons
    
    def wait_until_pt_icon_appear(self, skip_first_screenshot=True):
        """
        After entering event shop page,
        items are not loaded that fast,
        wait until any pt icon appears
        """
        timeout = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_info_bar():
                timeout.reset()
                continue

            MEDAL_SHOP_SCROLL.set_top(main=self)

            self.record_pt_icon()
            icons = self._get_pt_icons()

            if timeout.reached():
                break
            if len(icons) in [1, 2]:
                break

    @cached_property
    def shop_grid(self):
        return self.shop_event_grid()
    
    def shop_event_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        # (472, 348, 1170, 648)
        icons = self._get_pt_icons()
        count = len(icons)
        if count == 0:
            logger.warning('Unable to find pt icon, assume item list is at top')
            origin_y = 246
            delta_y = 213
            row = 2
        elif count == 1:
            y_list = icons[:, 1]
            origin_y = y_list[0] + 348 - (372 - 246)
            delta_y = 213
            row = 1
        elif count == 2:
            y_list = icons[:, 1]
            y1, y2 = y_list[0], y_list[1]
            origin_y = min(y1, y2) + 348 - (372 - 246)
            delta_y = abs(y1 - y2)
            row = 2
        else:
            logger.warning(f'Unexpected pt icon match result: {[i for i in icons]}')
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

    @cached_property
    def shop_event_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_event_items = EventShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_event_items.load_template_folder(self.shop_template_folder)
        shop_event_items.pt_icon = self.pt_icon
        shop_event_items.cost_similarity = 0.4
        shop_event_items.price_ocr = PRICE_OCR
        return shop_event_items

    def shop_items(self):
        """
        Shared alias for all shops,
        so for @Config must define
        a unique alias as cover

        Returns:
            ShopItemGrid:
        """
        return self.shop_event_items

    def shop_currency(self):
        """
        Ocr shop event currency
        Then return event coin count

        Returns:
            int: event coin amount
        """
        self._currency = self.status_get_pt()
        logger.info(f'Event pt: {self._currency}')
        return self._currency

    def shop_check_custom_item(self, item):
        """
        Check a custom item that should be bought with specific option.

        Args:
            item: Item to check
        
        Returns:
            bool: whether item is custom
        """
        if self.config.EventShop_BuyShip:  # int value from 0 to 5
            if (not item.is_known_item()) and item.price == 8000:
                # check a custom item that cannot be template matched as color
                # and design constantly changes i.e. event ship
                logger.info(f'Item {item} is considered to be a event ship')
                if self._currency >= item.price\
                        and item.count + self.config.EventShop_BuyShip > item.total_count:
                    return True
        
        if self.config.EventShop_BuyGear:
            if (not item.is_known_item()) and item.total_count == 1 and item.price in [2000, 10000]:
                # SSR gear costs 2000 pt and UR gear costs 10000 pt.
                # check a custom item that cannot be template matched as color
                # and design constantly changes i.e. event gear
                logger.info(f'Item {item} is considered to be a event gear')
                if self._currency >= item.price:
                    return True

        if self.config.EventShop_BuySkinBox:
            if (not item.is_known_item()) and item.total_count == 10 and item.price == 2000:
                # check a custom item that cannot be template matched as color
                # and design constantly changes i.e. equip skin box
                logger.info(f'Item {item} is considered to be an equip skin box')
                if self._currency >= item.price:
                    return True
        
        return False

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
        Run Event Shop
        """
        # Base case; exit run if filter empty
        if not self.shop_filter:
            return

        # When called, expected to be in
        # correct Event Shop interface
        logger.hr('Event Shop', level=1)

        self.wait_until_pt_icon_appear()
        # Execute buy operations
        
        while 1:
            self.shop_buy()
            if MEDAL_SHOP_SCROLL.at_bottom(main=self):
                logger.info('Event shop reach bottom, stop')
                break
            else:
                MEDAL_SHOP_SCROLL.next_page(main=self, page=0.66)
                del_cached_property(self, 'shop_grid')
                del_cached_property(self, 'shop_event_items')
                continue
