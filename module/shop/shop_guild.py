from module.base.decorator import cached_property
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.shop.base import ShopBase, ShopItemGrid
from module.shop.shop_guild_select import *

OCR_SHOP_GUILD_COINS = Digit(SHOP_GUILD_COINS, letter=(255, 255, 255), name='OCR_SHOP_GUILD_COINS')


class GuildItemGrid(ShopItemGrid):
    def predict(self, image, name=True, amount=True, cost=False, price=False):
        super().predict(image, name, amount, cost, price)

        # Loop again, to add 'secondary_grid' attr
        # only applicable to GuildShop items
        for item in self.items:
            name = item.name[0:-2].lower()
            if name in SELECT_ITEMS:
                item.secondary_grid = name
            else:
                item.secondary_grid = None

        return self.items


class GuildShop(ShopBase):
    _shop_guild_coins = 0

    def shop_get_guild_coins(self):
        self._shop_guild_coins = OCR_SHOP_GUILD_COINS.ocr(self.device.image)
        logger.info(f'Guild coins: {self._shop_guild_coins}')

    @cached_property
    def shop_guild_items(self):
        """
        Returns:
            GuildItemGrid:
        """
        shop_grid = self.shop_grid
        shop_guild_items = GuildItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_guild_items.load_template_folder('./assets/guild_shop')
        shop_guild_items.load_cost_template_folder('./assets/shop_cost')
        return shop_guild_items

    def shop_get_select_button(self, category='none', choice='none'):
        """
        Returns:
            Button:
        """
        # Ensure there is valid SELECT combination according to category
        try:
            choices = globals()[f'SELECT_{category.upper()}']
        except KeyError:
            logger.warn('Category \'{category}\' is invalid, no button could be retrieved')
            return None

        # Retrieve the correct SELECT_GRID based on category
        if category == 'book':
            shop_select_grid = SELECT_GRID_3X1
        elif category == 'tech' or \
                category == 'retrofit' or \
                (category == 'priority' and
                 (self.appear(SHOP_SELECT_PR2) or self.appear(SHOP_SELECT_PR3))):
            shop_select_grid = SELECT_GRID_4X1
        elif category == 'priority' and self.appear(SHOP_SELECT_PR1):
            shop_select_grid = SELECT_GRID_6X1
        else:
            shop_select_grid = SELECT_GRID_5X1

        # Utilize known fixed location for correct item
        if choice in choices:
            return shop_select_grid.buttons()[choices.get(choice)]

        logger.warn(f'Choice \'{choice}\' is invalid for Category \'{category}\', no button could be retrieved')
        return None
