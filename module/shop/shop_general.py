from module.base.decorator import cached_property
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.shop.base import ShopBase, ShopItemGrid

OCR_SHOP_GOLD_COINS = Digit(SHOP_GOLD_COINS, letter=(239, 239, 239), name='OCR_SHOP_GOLD_COINS')


class GeneralShop(ShopBase):
    _shop_gold_coins = 0

    def shop_get_gold_coins(self):
        self._shop_gold_coins = OCR_SHOP_GOLD_COINS.ocr(self.device.image)
        logger.info(f'Gold coins: {self._shop_gold_coins}')

    @cached_property
    def shop_general_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_general_items = ShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_general_items.load_template_folder('./assets/general_shop')
        shop_general_items.load_cost_template_folder('./assets/shop_cost')
        return shop_general_items
