from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.shop.base import ShopBase, ShopItemGrid

OCR_SHOP_MERIT = Digit(SHOP_MERIT, letter=(239, 239, 239), name='OCR_SHOP_MERIT')


class MeritShop(ShopBase):
    _shop_merit = 0

    @cached_property
    def shop_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_merit_items = ShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_merit_items.load_template_folder('./assets/shop/merit')
        shop_merit_items.load_cost_template_folder('./assets/shop/cost')
        return shop_merit_items

    def shop_currency(self):
        """
        Ocr shop merit currency

        Returns:
            int: merit amount
        """
        self._shop_merit = OCR_SHOP_MERIT.ocr(self.device.image)
        logger.info(f'Merit: {self._shop_merit}')
        return self._shop_merit

    def shop_check_item(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool:
        """
        if item.price > self._shop_merit:
            return False
        return True
