import cv2

from module.base.decorator import cached_property
from module.base.utils import color_similar
from module.logger import logger
from module.shop.base import ShopItemGrid_250814 as BaseShopItemGrid_250814
from module.shop.clerk import ShopClerk
from module.shop.shop_status import ShopStatus
from module.shop.ui import ShopUI


class ShopItemGrid_250814(BaseShopItemGrid_250814):
    SHIP_PRICES = {20000, 8000, 5000, 4000}

    @staticmethod
    def predict_tag(image):
        color = cv2.mean(image)[:3]
        if color_similar(color, (255, 72, 72), threshold=50):
            return 'unobtained'
        return None

    def predict(self, image, name=True, amount=True, cost=False, price=False, tag=False):
        items = super().predict(image, name, amount, cost, price, tag=True)
        for item in items:
            item.is_unobtained_ship = item.tag == 'unobtained' and item.price in self.SHIP_PRICES
        return items


class MeritShop_250814(ShopClerk, ShopUI, ShopStatus):
    shop_template_folder = './assets/shop/merit'

    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return self.config.MeritShop_Filter.strip()

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
            price_area=(18, 121, 85, 150),
            tag_area=(81, 4, 91, 8),
        )
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

    def shop_check_custom_item(self, item):
        if not self.config.MeritShop_BuyUnobtainedShip:
            return False
        if not getattr(item, 'is_unobtained_ship', False):
            return False
        if item.cost != 'Merit' or item.price > self._currency:
            return False

        logger.info(f'Item {item} is considered to be an unobtained ship')
        return True

    def run(self):
        """
        Run Merit Shop
        """
        # Base case; exit run if filter and custom-item purchase are both disabled
        if not self.shop_filter and not self.config.MeritShop_BuyUnobtainedShip:
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
