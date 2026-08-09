from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property
from module.base.template import Template
from module.logger import logger
from module.map_detection.utils import Points
from module.shop.assets import *
from module.shop.base import ShopItemGrid, ShopItemGrid_250814
from module.shop.clerk import ShopClerk
from module.shop.shop_medal import ShopScroll
from module.shop.shop_status import ShopStatus

TEMPLATE_CORE_ICON = Template('./assets/shop/cost/Core_4.png')


class CoreShopScroll(ShopScroll):
    def position_to_screen(self, position, random_range=(-0.01, 0.01)):
        return super().position_to_screen(position, random_range=random_range)


CORE_SHOP_SCROLL_250814 = CoreShopScroll(
    MEDAL_SHOP_SCROLL_AREA_250814.button,
    color=(44, 48, 56),
    name='CORE_SHOP_SCROLL_250814'
)
# Core shop has a much shorter slider than medal shop, keep the drag accurate
# enough to leave overlap between pages
CORE_SHOP_SCROLL_250814.drag_threshold = 0.03
CORE_SHOP_SCROLL_LIMIT = 20


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
        for _ in range(CORE_SHOP_SCROLL_LIMIT):
            # Execute buy operations
            if not self.shop_buy():
                break

            if CORE_SHOP_SCROLL_250814.at_bottom(main=self):
                logger.info('Core shop reach bottom, stop')
                break

            CORE_SHOP_SCROLL_250814.next_page(main=self, page=0.66)
            self.device.click_record_remove(CORE_SHOP_SCROLL_250814.name)
            del_cached_property(self, 'shop_grid')
            del_cached_property(self, 'shop_core_items')
        else:
            logger.warning('Too many pages in core shop, stopped')
