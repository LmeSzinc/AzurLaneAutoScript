from module.base.decorator import cached_property
from module.logger import logger
from module.shop.base import ShopItemGrid, ShopItemGrid_250814
from module.shop.clerk import ShopClerk
from module.shop.shop_status import ShopStatus
from module.shop.ui import ShopUI


class MeritShop(ShopClerk, ShopUI, ShopStatus):
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


class MeritShop_250814(MeritShop):
    # New UI in 2025-08-14
    @cached_property
    def shop_merit_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_merit_items = ShopItemGrid_250814(
            shop_grid,
            templates={},
            template_area=(25, 20, 82, 72),
            amount_area=(42, 50, 65, 65),
            cost_area=(-12, 115, 60, 155),
            price_area=(14, 121, 85, 150),
        )
        shop_merit_items.load_template_folder(self.shop_template_folder)
        shop_merit_items.load_cost_template_folder('./assets/shop/cost')
        return shop_merit_items
