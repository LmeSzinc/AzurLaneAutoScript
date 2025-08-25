from module.base.decorator import cached_property
from module.logger import logger
from module.shop.assets import *
from module.shop.base import ShopItemGrid, ShopItemGrid_250814
from module.shop.clerk import ShopClerk
from module.shop.shop_status import ShopStatus


class CoreShop(ShopClerk, ShopStatus):
    shop_template_folder = './assets/shop/core'

    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return self.config.CoreShop_Filter.strip()

    @cached_property
    def shop_core_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_core_items = ShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
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

        # Execute buy operations
        self.shop_buy()


class CoreShop_250814(CoreShop):
    # New UI in 2025-08-14
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
