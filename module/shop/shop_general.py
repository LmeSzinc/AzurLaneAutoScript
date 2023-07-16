from module.base.decorator import cached_property
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.shop.base import ShopItemGrid
from module.shop.clerk import ShopClerk
from module.shop.shop_status import ShopStatus
from module.shop.ui import ShopUI

OCR_SHOP_GOLD_COINS = Digit(SHOP_GOLD_COINS, letter=(239, 239, 239), name='OCR_SHOP_GOLD_COINS')
OCR_SHOP_GEMS = Digit(SHOP_GEMS, letter=(255, 243, 82), name='OCR_SHOP_GEMS')


class GeneralShop(ShopClerk, ShopUI, ShopStatus):
    gems = 0
    shop_template_folder = './assets/shop/general'

    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return self.config.GeneralShop_Filter.strip()

    @cached_property
    def shop_general_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_general_items = ShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_general_items.load_template_folder(self.shop_template_folder)
        shop_general_items.load_cost_template_folder('./assets/shop/cost')
        return shop_general_items

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
        return self.shop_general_items

    currency_rechecked = 0

    def shop_currency(self):
        """
        Ocr shop guild currency if needed
        (gold coins and gems)
        Then return gold coin count

        Returns:
            int: gold coin amount
        """
        while 1:
            self._currency = self.status_get_gold_coins()
            self.gems = self.status_get_gems()
            logger.info(f'Gold coins: {self._currency}, Gems: {self.gems}')

            if self.currency_rechecked >= 3:
                logger.warning('Failed to handle fix currency bug in general shop, skip')
                break

            # if self._currency == 0 and self.gems == 0:
            #     logger.info('Game bugged, coins and gems disappeared, switch between shops to reset')
            #     self.currency_rechecked += 1
            #
            #     # 2022.06.01 General shop no longer at an expected location
            #     # NavBar 'get_active' (0 index-based) and swap with its left
            #     # adjacent neighbor then back (NavBar 'set' is 1 index-based)
            #     index = self._shop_bottom_navbar.get_active(self)
            #     self.shop_bottom_navbar_ensure(left=index)
            #     self.shop_bottom_navbar_ensure(left=index + 1)
            #     continue
            # else:
            #     break
            # 2023.07.13 Shop UI changed entirely, remove all these
            break

        return self._currency

    def shop_check_item(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool: whether item can be bought
        """
        if item.cost == 'Coins':
            if item.price > self._currency:
                return False
            return True

        if self.config.GeneralShop_UseGems:
            if item.cost == 'Gems':
                if item.price > self.gems:
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
                if self._currency >= item.price:
                    return True

        return False

    def run(self):
        """
        Run General Shop
        """
        # Base case; exit run if filter empty
        if not self.shop_filter:
            return

        # When called, expected to be in
        # corrected General Shop interface
        logger.hr('General Shop', level=1)

        # Execute buy operations
        # Refresh if enabled and available
        refresh = self.config.GeneralShop_Refresh
        for _ in range(2):
            success = self.shop_buy()
            if not success:
                break
            if refresh and self.shop_refresh():
                continue
            break
