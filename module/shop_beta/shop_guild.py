from module.base.decorator import Config
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1, GET_SHIP
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.shop.base import ShopBase, ShopItemGrid
from module.shop.shop_guild_globals import *
from module.ui.assets import BACK_ARROW
from module.shop.ui import ShopUI

SHOP_SELECT_PR = [SHOP_SELECT_PR1, SHOP_SELECT_PR2, SHOP_SELECT_PR3]

OCR_SHOP_GUILD_COINS = Digit(SHOP_GUILD_COINS, letter=(255, 255, 255), name='OCR_SHOP_GUILD_COINS')
OCR_SHOP_SELECT_TOTAL_PRICE = Digit(SHOP_SELECT_TOTAL_PRICE, letter=(255, 255, 255), name='OCR_SHOP_SELECT_TOTAL_PRICE')


class GuildItemGrid(ShopItemGrid):
    def predict(self, image, name=True, amount=True, cost=False, price=False, tag=False):
        """
        Overridden to iterate and add attribute for items classified as having
        secondary grid and additional information
        """
        super().predict(image, name, amount, cost, price, tag)

        # Loop again for Guild Shop items
        # Add attr 'secondary_grid' used to flag and id
        # Add attr 'additional' to id specific config
        # if applicable
        for item in self.items:
            # Defaults
            item.secondary_grid = None
            item.additional = None

            name = item.name[:-2].lower()
            if name in SELECT_ITEMS:
                item.secondary_grid = name
                if name != 'pr' and name != 'dr':
                    item.additional = item.name[-2:]

        return self.items


class GuildShop(ShopBase, ShopUI):
    _shop_guild_coins = 0

    @cached_property
    @Config.when(SERVER='cn')
    def shop_items(self):
        """
        Returns:
            GuildItemGrid:
        """
        shop_grid = self.shop_grid
        shop_guild_items = GuildItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_guild_items.load_template_folder('./assets/shop/guild_cn')
        shop_guild_items.load_cost_template_folder('./assets/shop/cost')
        return shop_guild_items

    @cached_property
    @Config.when(SERVER='tw')
    def shop_items(self):
        """
        Returns:
            GuildItemGrid:
        """
        shop_grid = self.shop_grid
        shop_guild_items = GuildItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_guild_items.load_template_folder('./assets/shop/guild_cn')
        shop_guild_items.load_cost_template_folder('./assets/shop/cost')
        return shop_guild_items

    @cached_property
    @Config.when(SERVER=None)
    def shop_items(self):
        """
        Returns:
            GuildItemGrid:
        """
        shop_grid = self.shop_grid
        shop_guild_items = GuildItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_guild_items.load_template_folder('./assets/shop/guild')
        shop_guild_items.load_cost_template_folder('./assets/shop/cost')
        return shop_guild_items

    def shop_currency(self):
        """
        Returns:
            int:
        """
        self._shop_guild_coins = OCR_SHOP_GUILD_COINS.ocr(self.device.image)
        logger.info(f'Guild coins: {self._shop_guild_coins}')
        return self._shop_guild_coins

    def shop_check_item(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool: whether item can be bought
        """
        if item.price > self._shop_guild_coins:
            return False
        return True

    def shop_get_select(self, category, choice):
        """
        Args:
            category: String identifies SELECT combination
            choice (string, list): String identifies index within SELECT combination
                                   List types exclusively for PR series selection

        Returns:
            Button:
        """
        # Ensure there is valid SELECT combination according to category
        try:
            choices = globals()[f'SELECT_{category.upper()}']
        except KeyError:
            logger.warning(f'shop_get_select --> Missing SELECT_{category.upper()}')
            return None

        # Retrieve the correct SELECT_GRID based on category
        shop_select_grid = None
        if category == 'book':
            shop_select_grid = SELECT_GRID_3X1
        elif category == 'box' or category == 'retrofit':
            shop_select_grid = SELECT_GRID_4X1
        elif category == 'pr' and isinstance(choice, list):
            # Determine series of PR is displayed
            # Position of successful appearance
            # determines correct shop_select_grid
            results = [self.appear(button, offset=(20, 20)) for button in SHOP_SELECT_PR]
            for idx, result in enumerate(results):
                if result:
                    choice = choice[idx]
                    if idx == 0:
                        shop_select_grid = SELECT_GRID_6X1
                    else:
                        shop_select_grid = SELECT_GRID_4X1
                    break
        elif category == 'plate':
            shop_select_grid = SELECT_GRID_5X1

        if shop_select_grid is None:
            logger.warning(f'shop_get_select --> No grid applicable to category \'{category}\'')
            return None

        # Utilize known fixed location for correct item
        if choice in choices:
            return shop_select_grid.buttons[choices.get(choice)]

        logger.warning(f'shop_get_select --> Missing \'{choice}\' in SELECT_{category.upper()}')
        return None

    def shop_buy_select_execute(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool: implicating failed to execute
        """
        # Base Case - Must have 'secondary_grid' attr and must not be None
        if not hasattr(item, 'secondary_grid') or item.secondary_grid is None:
            logger.warning('shop_buy_select_execute --> Detected secondary '
                           'prompt but item not classified of having this option')
            self.device.click(SHOP_CLICK_SAFE_AREA)  # Close secondary prompt
            return False

        # Proceed and verify required components can be acquired
        category = item.secondary_grid
        additional = '' if item.additional is None else f'_{item.additional}'
        try:
            limit = globals()[f'SELECT_{category.upper()}_LIMIT']
            choice = getattr(self.config, f'GuildShop_{category.upper()}{additional.upper()}')
        except KeyError:
            logger.warning(f'shop_buy_select_execute --> Missing SELECT_{category.upper()}_LIMIT')
            self.device.click(SHOP_CLICK_SAFE_AREA)  # Close secondary prompt
            return False
        except AttributeError:
            logger.warning(f'shop_buy_select_execute --> Missing Config GuildShop_{category.upper()}{additional.upper()}')
            self.device.click(SHOP_CLICK_SAFE_AREA)  # Close secondary prompt
            return False

        # Find and click appropriate button within secondary grid
        # This results in plus/minus appearing, click until those appear
        select = self.shop_get_select(category, choice)
        click_timer = Timer(3, count=6)
        select_offset = (500, 400)
        while 1:
            if select is not None:
                if click_timer.reached():
                    self.device.click(select)
                    click_timer.reset()
            else:
                self.device.click(SHOP_CLICK_SAFE_AREA)  # Close secondary prompt
                return False

            # Scan for plus/minus locations varies based on grid and item selected
            # After searching within an offset, buttons move to the actual location automatically.
            self.device.screenshot()
            if self.appear(SELECT_MINUS, offset=select_offset) and self.appear(SELECT_PLUS, offset=select_offset):
                break
            else:
                continue

        # Total number to purchase altogether
        while 1:
            if (limit * item.price) <= self._shop_guild_coins:
                break
            else:
                limit -= 1

        # For ui_ensure_index to calculate amount/count
        # representation of total_price
        def total_price_to_count(image):
            total_price = OCR_SHOP_SELECT_TOTAL_PRICE.ocr(image)
            return int(total_price / item.price)

        self.ui_ensure_index(limit, letter=total_price_to_count, prev_button=SELECT_MINUS, next_button=SELECT_PLUS,
                             skip_first_screenshot=True)
        self.device.click(SHOP_BUY_CONFIRM_SELECT)
        return True

    def shop_interval_clear(self):
        """
        Clear interval on select assets for
        shop_buy_handle
        """
        self.interval_clear(SHOP_BUY_CONFIRM_SELECT)

    def shop_buy_handle(self, item):
        """
        Handle shop_guild buy interface if detected

        Args:
            item: Item to handle

        Returns:
            bool: whether interface was detected and handled
        """
        if self.appear(SHOP_BUY_CONFIRM_SELECT, offset=(20, 20), interval=3):
            if not self.shop_buy_select_execute(item):
                logger.warning('Failed to purchase secondary '
                               'grid item')
            self.interval_reset(SHOP_BUY_CONFIRM_SELECT)
            return True

        return False

    def run(self):
        """
        Run Guild Shop
        """
        # Base case; exit run if empty
        selection = str(self.config.GuildShop_Filter)
        if not selection.strip():
            return

        # When called, expected to be in
        # correct Guild Shop interface
        logger.hr('Guild Shop', level=1)

        # Execute buy operations
        # Refresh if enabled and available
        refresh = self.config.GuildShop_Refresh
        for _ in range(2):
            success = self.shop_buy(selection=selection)
            if not success:
                break
            if refresh and self.shop_refresh():
                continue
            break
