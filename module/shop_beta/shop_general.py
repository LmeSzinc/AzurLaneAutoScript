from module.base.decorator import cached_property
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.shop.base import ShopBase, ShopItemGrid
from module.shop.ui import ShopUI

OCR_SHOP_GOLD_COINS = Digit(SHOP_GOLD_COINS, letter=(239, 239, 239), name='OCR_SHOP_GOLD_COINS')
OCR_SHOP_GEMS = Digit(SHOP_GEMS, letter=(255, 243, 82), name='OCR_SHOP_GEMS')


class GeneralShop(ShopBase, ShopUI):
    _shop_gold_coins = 0
    _shop_gems = 0

    @cached_property
    def shop_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_general_items = ShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_general_items.load_template_folder('./assets/shop/general')
        shop_general_items.load_cost_template_folder('./assets/shop/cost')
        return shop_general_items

    def shop_currency(self):
        """
        Returns:
            int: gold coin amount
        """
        self._shop_gold_coins = OCR_SHOP_GOLD_COINS.ocr(self.device.image)
        self._shop_gems = OCR_SHOP_GEMS.ocr(self.device.image)
        logger.info(f'Gold coins: {self._shop_gold_coins}, Gems: {self._shop_gems}')
        return self._shop_gold_coins

    def shop_check_item(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool: whether item can be bought
        """
        if item.cost == 'Coins':
            if item.price > self._shop_gold_coins:
                return False
            return True

        if self.config.GeneralShop_UseGems:
            if item.cost == 'Gems':
                if item.price > self._shop_gems:
                    return False
                return True

        return False

    def shop_check_custom_item(self, item):
        """
        Optional def to check a custom item that
        cannot be template matched as color and
        design constantly changes i.e. equip skin box

        Args:
            item: Item to check

        Returns:
            bool: whether item is custom
        """
        if self.config.GeneralShop_BuySkinBox:
            if (not item.is_known_item()) and item.amount == 1 and item.cost == 'Coins' and item.price == 7000:
                logger.info(f'Item {item} is considered to be an equip skin box')
                if self._shop_gold_coins >= item.price:
                    return True

        return False

    def run(self):
        """
        Run General Shop
        """
        # Base case; exit run if empty
        selection = self.config.GeneralShop_Filter
        if not selection.strip():
            return

        # Route to General Shop
        logger.hr('General Shop', level=1)
        self.ui_goto_shop()
        if not self.shop_bottom_navbar_ensure(left=5):
            logger.warning('Failed to transition to shop, skipping')
            return

        # Execute buy operations
        # Refresh if enabled and available
        refresh = self.config.GeneralShop_Refresh
        for _ in range(2):
            success = self.shop_buy(selection=selection)
            if not success:
                break
            if refresh and self.shop_refresh():
                continue
            break
