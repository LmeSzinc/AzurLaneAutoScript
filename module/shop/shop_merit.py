from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.shop.base import ShopBase, ShopItemGrid

OCR_SHOP_MERIT = Digit(SHOP_MERIT, letter=(239, 239, 239), name='OCR_SHOP_MERIT')


class MeritShop(ShopBase):
    _shop_merit = 0

    def shop_get_merit(self):
        self._shop_merit = OCR_SHOP_MERIT.ocr(self.device.image)
        logger.info(f'Merit: {self._shop_merit}')

    @cached_property
    def shop_merit_grid(self):
        shop_grid = ButtonGrid(
            origin=(477, 365), delta=(156, 0), button_shape=(96, 96), grid_shape=(5, 1), name='SHOP_MERIT_GRID')
        return shop_grid

    @cached_property
    def shop_merit_items(self):
        """
        Returns:
            ItemGrid:
        """
        shop_grid = self.shop_merit_grid
        shop_merit_items = ShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_merit_items.load_template_folder('./assets/merit_shop')
        shop_merit_items.load_cost_template_folder('./assets/shop_cost')
        return shop_merit_items
