from module.base.decorator import cached_property
from module.logger import logger
from module.shop.assets import *
from module.shop.base import ShopItemGrid
from module.shop.clerk import ShopClerk
from module.shop.shop_status import ShopStatus
from module.shop.ui import ShopUI

import module.config.server as server

class GuildShop(ShopClerk, ShopUI, ShopStatus, server):
    if server in ['cn', 'en', 'jp']:
        shop_template_folder = './assets/shop/guild_white'

    if server in ['tw']:
        shop_template_folder = './assets/shop/guild'

    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return self.config.GuildShop_Filter.strip()

    @cached_property
    def shop_guild_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_guild_items = ShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        if server in ['cn', 'en', 'jp']:
            self.shop_template_folder = './assets/shop/guild_white'
        if server in ['tw']:
            self.shop_template_folder = './assets/shop/guild'
        shop_guild_items.load_template_folder(self.shop_template_folder)
        if server in ['cn', 'en', 'jp']:
            shop_guild_items.load_cost_template_folder('./assets/shop/cost_white')
        if server in ['tw']:
            shop_guild_items.load_cost_template_folder('./assets/shop/cost')
        return shop_guild_items

    def shop_items(self):
        """
        Shared alias for all shops,
        so for @Config must define
        a unique alias as cover

        Returns:
            ShopItemGrid:
        """
        return self.shop_guild_items

    def shop_currency(self):
        """
        Ocr shop guild currency
        Then return guild coin count

        Returns:
            int: guild coin amount
        """
        self._currency = self.status_get_guild_coins()
        logger.info(f'Guild coins: {self._currency}')
        return self._currency

    def shop_interval_clear(self):
        """
        Clear interval on select assets for
        shop_buy_handle
        """
        super().shop_interval_clear()
        self.interval_clear(SHOP_BUY_CONFIRM_SELECT)

    def shop_buy_handle(self, item):
        """
        Handle shop_guild buy interface if detected

        Args:
            item: Item to handle

        Returns:
            bool: whether interface was detected and handled
        """
        if self.appear(SHOP_BUY_CONFIRM_SELECT, offset=(20, 20), interval=3):
            self.shop_buy_select_execute(item)
            self.interval_reset(SHOP_BUY_CONFIRM_SELECT)
            return True

        return False

    def run(self):
        """
        Run Guild Shop
        """
        # Base case; exit run if filter empty
        if not self.shop_filter:
            return

        # When called, expected to be in
        # correct Guild Shop interface
        logger.hr('Guild Shop', level=1)

        # Execute buy operations
        # Refresh if enabled and available
        refresh = self.config.GuildShop_Refresh
        for _ in range(2):
            success = self.shop_buy()
            if not success:
                break
            if refresh:
                # Refresh costs 50 and PlateT4 costs 60
                if self._currency >= 110:
                    if self.shop_refresh():
                        continue
                else:
                    logger.info('Guild coins < 110, skip refreshing')
            break
