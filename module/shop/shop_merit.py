import cv2

from module.base.decorator import cached_property
from module.base.utils import color_similarity_2d
from module.logger import logger
from module.shop.base import ShopItemGrid, ShopItemGrid_250814
from module.shop.clerk import ShopClerk
from module.shop.shop_status import ShopStatus
from module.shop.ui import ShopUI


class ShopItemGrid_250814_Unget(ShopItemGrid_250814):
    """
    Shop item grid with unget ribbon detection for Merit Shop.

    Items that haven't been obtained show a red ribbon at the top right of
    the card. Ribbon overflows the 64px button, detection runs on the left
    part of it which remains inside the 96x96 item image.
    """

    RIBBON_AREA = (56, 0, 96, 48)
    UNGET_COLOR = (249, 91, 103)  # RGB, mean color of ribbon red
    UNGET_SIMILARITY = 180
    UNGET_COUNT = 50

    def predict(self, image, name=True, amount=True, cost=False, price=False, tag=False):
        items = super().predict(image, name, amount, cost, price, tag)
        for item in items:
            if self.predict_ribbon(item):
                logger.info(f'Item {item} has unget ribbon, rename to Unget')
                item.name = 'Unget'
                item.group = 'unget'
        return items

    def predict_ribbon(self, item):
        """
        Count pixels similar to ribbon red at the top right corner of item image.

        Args:
            item (Item):

        Returns:
            bool: If unget ribbon detected.
        """
        x1, y1, x2, y2 = self.RIBBON_AREA
        roi = item.image[y1:y2, x1:x2]
        mask = color_similarity_2d(roi, color=self.UNGET_COLOR)
        cv2.inRange(mask, self.UNGET_SIMILARITY, 255, dst=mask)
        return cv2.countNonZero(mask) > self.UNGET_COUNT


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
        shop_merit_items = ShopItemGrid_250814_Unget(
            shop_grid,
            templates={},
            template_area=(25, 20, 82, 72),
            amount_area=(42, 50, 65, 65),
            cost_area=(-12, 115, 60, 155),
            price_area=(18, 121, 85, 150),
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
