from module.base.button import ButtonGrid
from module.base.decorator import Config
from module.base.decorator import cached_property
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.shop.base import ShopBase, ShopItemGrid

OCR_SHOP_MEDAL = Digit(SHOP_MEDAL, letter=(239, 239, 239), name='OCR_SHOP_MEDAL')


class MedalShop(ShopBase):
    _shop_medal = 0

    def shop_medal_get_currency(self):
        """
        Ocr shop medal currency
        """
        self._shop_medal = OCR_SHOP_MEDAL.ocr(self.device.image)
        logger.info(f'Medal: {self._shop_medal}')

    @cached_property
    def shop_medal_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        shop_grid = ButtonGrid(
            origin=(197, 193), delta=(223, 190), button_shape=(100.5, 101.5), grid_shape=(3, 2), name='SHOP_MEDAL_GRID')
        return shop_grid

    @cached_property
    @Config.when(SERVER='jp')
    def shop_medal_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        # JP has thinner letters, increase threshold to 128
        price_ocr = Digit([], letter=(255, 223, 57), threshold=128, name='Price_ocr')
        shop_grid = self.shop_medal_grid
        shop_medal_items = ShopItemGrid(
            shop_grid, templates={}, amount_area=(60, 74, 96, 95), price_area=(52, 135, 132, 162))
        shop_medal_items.load_template_folder('./assets/shop/medal')
        shop_medal_items.load_cost_template_folder('./assets/shop/cost')
        shop_medal_items.similarity = 0.88  # Lower the threshold for consistent matches of PR/DRBP
        shop_medal_items.price_ocr = price_ocr
        return shop_medal_items

    @cached_property
    @Config.when(SERVER=None)
    def shop_medal_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_medal_grid
        shop_medal_items = ShopItemGrid(
            shop_grid, templates={}, amount_area=(60, 74, 96, 95), price_area=(52, 134, 132, 162))
        shop_medal_items.load_template_folder('./assets/shop/medal')
        shop_medal_items.load_cost_template_folder('./assets/shop/cost')
        shop_medal_items.similarity = 0.88  # Lower the threshold for consistent matches of PR/DRBP
        return shop_medal_items

    @cached_property
    def shop_medal_default_price(self):
        """
        return default price shows when shop items loading is not finished

        Returns:
            int
        """
        return 5000

    def shop_medal_check_item(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool:
        """
        if item.price > self._shop_medal:
            return False
        return True
