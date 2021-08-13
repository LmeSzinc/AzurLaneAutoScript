from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.shop.base import ShopBase, ShopItemGrid

OCR_SHOP_MERIT = Digit(SHOP_MERIT, letter=(239, 239, 239), name='OCR_SHOP_MERIT')


class MeritShop(ShopBase):
    _shop_merit = 0

    def shop_merit_get_currency(self):
        """
        Ocr shop merit currency
        """
        self._shop_merit = OCR_SHOP_MERIT.ocr(self.device.image)
        logger.info(f'Merit: {self._shop_merit}')

    @cached_property
    def shop_merit_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_merit_items = ShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_merit_items.load_template_folder('./assets/shop/merit')
        shop_merit_items.load_cost_template_folder('./assets/shop/cost')
        return shop_merit_items

    def shop_merit_check_item(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool:
        """
        if item.price > self._shop_merit:
            return False
        return True
