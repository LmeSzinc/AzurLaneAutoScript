import cv2
import numpy as np

from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property
from module.base.template import Template
from module.logger import logger
from module.map_detection.utils import Points
from module.shop.assets import *
from module.shop.base import ShopItemGrid, ShopItemGrid_250814
from module.shop.clerk import ShopClerk
from module.shop.shop_status import ShopStatus

TEMPLATE_CORE_ICON = Template('./assets/shop/cost/Core_4.png')
# Item list, used to swipe and to tell whether list has moved
CORE_SHOP_ITEM_AREA = (220, 195, 1050, 640)
# About 1.7 rows, small enough not to skip a row, large enough to make progress
CORE_SHOP_SWIPE_DISTANCE = 380


class CoreShop_250814(ShopClerk, ShopStatus):
    shop_template_folder = './assets/shop/core'

    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return self.config.CoreShop_Filter.strip()

    # New UI in 2025-08-14
    def _get_cores(self):
        """
        Returns:
            np.array: [[x1, y1], [x2, y2]], location of the core icon upper-left corner.
        """
        area = (250, 190, 1000, 645)
        # copy image because matchTemplate needs a continuous array
        image = self.image_crop(area, copy=True)
        cores = TEMPLATE_CORE_ICON.match_multi(image, similarity=0.8, threshold=5)
        cores = Points([(0., c.area[1]) for c in cores]).group(threshold=5)
        logger.attr('Core_icon', len(cores))
        return cores

    @cached_property
    def shop_grid(self):
        """
        Item rows are only aligned with the static grid when list is at top,
        so locate them by the core icon in price bar, like medal shop does.

        Returns:
            ButtonGrid:
        """
        cores = self._get_cores()
        count = len(cores)
        if count == 0:
            logger.warning('Unable to find core icon, assume item list is at top')
            origin_y = 238
            delta_y = 223
            row = 2
        elif count == 1:
            y_list = cores[:, 1]
            # +190, top of the crop area in _get_cores()
            # -129, from the top of core icon to the top of shop item
            origin_y = y_list[0] + 190 - 129
            delta_y = 223
            row = 1
        elif count == 2:
            y_list = cores[:, 1]
            y1, y2 = y_list[0], y_list[1]
            origin_y = min(y1, y2) + 190 - 129
            delta_y = abs(y1 - y2)
            row = 2
        else:
            logger.warning(f'Unexpected core icon match result: {[c for c in cores]}')
            origin_y = 238
            delta_y = 223
            row = 2

        shop_grid = ButtonGrid(
            origin=(265, origin_y), delta=(169, delta_y), button_shape=(64, 64), grid_shape=(5, row),
            name='SHOP_GRID')
        return shop_grid

    @cached_property
    def shop_core_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_core_items = ShopItemGrid_250814(
            shop_grid,
            templates={},
            template_area=(25, 20, 82, 72),
            amount_area=(42, 50, 65, 65),
            cost_area=(-12, 115, 60, 155),
            price_area=(18, 121, 85, 150),
        )
        shop_core_items.load_template_folder(self.shop_template_folder)
        shop_core_items.load_cost_template_folder('./assets/shop/cost')
        return shop_core_items

    def shop_items(self):
        """
        Shared alias for all shops
        If there are server-lang
        differences, reference
        shop_guild/medal for @Config
        example

        Returns:
            ShopItemGrid:
        """
        return self.shop_core_items

    def shop_currency(self):
        """
        Ocr shop core currency
        Then return core count

        Returns
            int: core amount
        """
        self._currency = self.status_get_core()
        logger.info(f'Core: {self._currency}')
        return self._currency

    def shop_interval_clear(self):
        """
        Clear interval on select assets for
        shop_core_buy_handle
        """
        super().shop_interval_clear()
        self.interval_clear(SHOP_BUY_CONFIRM_AMOUNT)

    def shop_buy_handle(self, item):
        """
        Handle shop_core buy interface if detected

        Args:
            item: Item to handle

        Returns:
            bool: whether interface was detected and handled
        """
        if self.appear(SHOP_BUY_CONFIRM_AMOUNT, offset=(20, 20), interval=3):
            self.shop_buy_amount_execute(item)
            self.interval_reset(SHOP_BUY_CONFIRM_AMOUNT)
            return True

        return False

    def shop_swipe(self, distance, name='CORE_SHOP_SWIPE'):
        """
        Swipe item list and tell whether it actually moved.

        Swiping the list instead of dragging the scrollbar, because the lower half
        of the scrollbar overlaps a dark character illustration and loses contrast
        there, making scroll position unreadable near the bottom.

        Args:
            distance (int): Pixels to swipe, negative to show following items.
            name (str):

        Returns:
            bool: True if item list moved, False if it already reached the end.
        """
        before = self.image_crop(CORE_SHOP_ITEM_AREA, copy=True)
        x = (CORE_SHOP_ITEM_AREA[0] + CORE_SHOP_ITEM_AREA[2]) // 2
        y = (CORE_SHOP_ITEM_AREA[1] + CORE_SHOP_ITEM_AREA[3]) // 2
        # drag instead of swipe, so the shake at the end cancels inertia,
        # otherwise list keeps sliding and skips rows that were never detected
        self.device.drag((x, y - distance // 2), (x, y + distance // 2), segments=2, shake=(0, 25),
                         point_random=(0, 0, 0, 0), shake_random=(0, -5, 0, 5), name=name)
        # Going through the whole list takes more swipes than the too-many-click
        # guard allows, drop them as they are expected repetitions
        self.device.click_record_remove(name)
        self.device.sleep(0.5)
        self.device.screenshot()
        after = self.image_crop(CORE_SHOP_ITEM_AREA, copy=True)

        # Item cards are static, moving the list gives a difference of tens
        difference = float(np.mean(cv2.absdiff(before, after)))
        moved = difference > 5
        logger.attr(name, f'{"moved" if moved else "stuck"}, difference={difference:.1f}')
        if moved:
            del_cached_property(self, 'shop_grid')
            del_cached_property(self, 'shop_core_items')
        return moved

    def shop_swipe_top(self):
        """
        Swipe item list back to top, so no item is missed no matter where the
        list was left at.
        """
        for _ in range(10):
            if not self.shop_swipe(CORE_SHOP_SWIPE_DISTANCE, name='CORE_SHOP_SWIPE_TOP'):
                return
        logger.warning('Failed to swipe core shop to top')

    def run(self):
        """
        Run Core Shop
        """
        # Base case; exit run if filter empty
        if not self.shop_filter:
            return

        # When called, expected to be in
        # correct Core Shop interface
        logger.hr('Core Shop', level=1)

        # Core monthly shop holds about 20 rows of items while only 2 rows are
        # visible, items must be scrolled through page by page
        self.shop_swipe_top()
        for _ in range(20):
            # Execute buy operations
            if not self.shop_buy():
                break

            if not self.shop_swipe(-CORE_SHOP_SWIPE_DISTANCE, name='CORE_SHOP_SWIPE_NEXT'):
                logger.info('Core shop reach bottom, stop')
                break
        else:
            logger.warning('Too many pages in core shop, stopped')
