from module.base.decorator import cached_property
from module.logger import logger
from module.shop.base import ShopItemGrid
from module.shop.clerk import ShopClerk
from module.shop.shop_status import ShopStatus
from module.shop.ui import ShopUI

import module.config.server as server


class MeritShop(ShopClerk, ShopUI, ShopStatus, server):
    if server in ['cn', 'en', 'jp']:
        shop_template_folder = './assets/shop/merit_white'

    if server in ['tw']:
        shop_template_folder = './assets/shop/merit'

    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return self.config.MeritShop_Filter.strip()

    @cached_property
    def shop_merit_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_merit_items = ShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_merit_items.load_template_folder(self.shop_template_folder)
        if server in ['cn', 'en', 'jp']:
            shop_merit_items.load_cost_template_folder('./assets/shop/cost_white')
        if server in ['tw']:
            shop_merit_items.load_cost_template_folder('./assets/shop/cost')
        return shop_merit_items

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
        return self.shop_merit_items

    def shop_currency(self):
        """
        Ocr shop merit currency
        Then return merit count

        Returns:
            int: merit amount
        """
        self._currency = self.status_get_merit()
        logger.info(f'Merit: {self._currency}')
        return self._currency

    def run(self):
        """
        Run Merit Shop
        """
        # Base case; exit run if filter empty
        if not self.shop_filter:
            return

        # When called, expected to be in
        # correct Merit Shop interface
        logger.hr('Merit Shop', level=1)

        # Execute buy operations
        # Refresh if enabled and available
        refresh = self.config.MeritShop_Refresh
        for _ in range(2):
            success = self.shop_buy()
            if not success:
                break
            if refresh and self.shop_refresh():
                continue
            break
