from module.base.button import ButtonGrid
from module.base.decorator import Config, cached_property
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.shop.base import ShopBase, ShopItemGrid

OCR_SHOP_MEDAL = Digit(SHOP_MEDAL, letter=(239, 239, 239), name="OCR_SHOP_MEDAL")


class MedalShop(ShopBase):
    _shop_medal = 0

    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return self.config.MedalShop_Filter.strip()

    @cached_property
    def shop_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        shop_grid = ButtonGrid(
            origin=(197, 193),
            delta=(223, 190),
            button_shape=(100.5, 100.5),
            grid_shape=(3, 2),
            name="SHOP_GRID",
        )
        return shop_grid

    @cached_property
    @Config.when(SERVER="jp")
    def shop_medal_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_medal_items = ShopItemGrid(
            shop_grid,
            templates={},
            amount_area=(60, 74, 96, 95),
            cost_area=(6, 123, 84, 175),
            price_area=(52, 135, 132, 162),
        )
        shop_medal_items.load_template_folder("./assets/shop/medal")
        shop_medal_items.load_cost_template_folder("./assets/shop/cost")
        shop_medal_items.similarity = (
            0.88  # Lower the threshold for consistent matches of PR/DRBP
        )
        # JP has thinner letters, so increase threshold to 128
        shop_medal_items.price_ocr = Digit(
            [], letter=(255, 223, 57), threshold=128, name="PRICE_OCR"
        )
        return shop_medal_items

    @cached_property
    @Config.when(SERVER=None)
    def shop_medal_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_medal_items = ShopItemGrid(
            shop_grid,
            templates={},
            amount_area=(60, 74, 96, 95),
            price_area=(52, 134, 132, 162),
        )
        shop_medal_items.load_template_folder("./assets/shop/medal")
        shop_medal_items.load_cost_template_folder("./assets/shop/cost")
        shop_medal_items.similarity = (
            0.88  # Lower the threshold for consistent matches of PR/DRBP
        )
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

        Returns:
            int: medal amount
        """
        self._shop_medal = OCR_SHOP_MEDAL.ocr(self.device.image)
        logger.info(f"Medal: {self._shop_medal}")
        return self._shop_medal

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

    def shop_check_item(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool:
        """
        if item.price > self._shop_medal:
            return False
        return True

    def run(self):
        """
        Run Medal Shop
        """
        # Base case; exit run if filter empty
        if not self.shop_filter:
            return

        # When called, expected to be in
        # correct Medal Shop interface
        logger.hr("Medal Shop", level=1)

        # Execute buy operations
        self.shop_buy()
