from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.shop.base import ShopBase, ShopItemGrid

OCR_SHOP_MEDAL = Digit(SHOP_MEDAL, letter=(239, 239, 239), name='OCR_SHOP_MEDAL')


class MedalShop(ShopBase):
    _shop_medal = 0

    def shop_medal_get_currency(self):
        self._shop_medal = OCR_SHOP_MEDAL.ocr(self.device.image)
        logger.info(f'Medal: {self._shop_medal}')

    @cached_property
    def shop_medal_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        shop_grid = ButtonGrid(
            origin=(197, 193), delta=(224, 191), button_shape=(101, 101), grid_shape=(3, 2), name='SHOP_MEDAL_GRID')
        return shop_grid

    @cached_property
    def shop_medal_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_medal_grid
        shop_medal_items = ShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_medal_items.load_template_folder('./assets/medal_shop')
        shop_medal_items.load_cost_template_folder('./assets/shop_cost')
        return shop_medal_items

    def shop_medal_check_item(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool:
        """
        if item.cost == 'Medal':
            if item.price > self._shop_medal:
                return False
            return True
        return False
