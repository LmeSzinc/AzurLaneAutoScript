from module.base.decorator import Config
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1, GET_SHIP
from module.exception import ScriptEnd
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
        Overridden to iterate, add attributes to assist with
        shop_*_select_* funcs
        """
        super().predict(image, name, amount, cost, price, tag)

        # Add attributes to assist with
        # shop_*_select_* funcs
        for item in self.items:
            if item.group is None:
                continue

            # Designate appropriate 'postfix' attr
            # for globals and config referencing
            lgroup = item.group.lower()
            if lgroup in SELECT_ITEMS:
                item.postfix = ''
                if lgroup != 'pr' and lgroup != 'dr':
                    item.postfix = f'_{item.tier.upper()}'

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
        Ocr shop guild currency

        Returns:
            int: guild coin amount
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

    def shop_get_select(self, item, choice):
        """
        Args:
            item (Item): Item for reference
            choice (str, list(str)):
                String identifies index within SELECT combination
                List types exclusively for PR/DR series selection

        Returns:
            Button:

        Raises:
            ScriptEnd:
        """
        # Ensure there is valid SELECT_* combination for item group
        # Stow variables for frequent usage
        lgroup = item.group.lower()
        ugroup = item.group.upper()
        try:
            choices = globals()[f'SELECT_{ugroup}']
        except KeyError:
            logger.critical(f'Missing SELECT_{ugroup} (global)')
            raise ScriptEnd

        # Choose the applicable SELECT_GRID_* for item group
        shop_select_grid = None
        if lgroup == 'book':
            shop_select_grid = SELECT_GRID_3X1
        elif lgroup == 'box' or lgroup == 'retrofit':
            shop_select_grid = SELECT_GRID_4X1
        elif lgroup == 'pr' and isinstance(choice, list):
            # Complex grid retrieval based on PR/DR series
            # Determine series through asset appearance
            # and convert choice from list(str) to str
            for idx, button in enumerate(SHOP_SELECT_PR):
                if self.appear(button, offset=(20, 20)):
                    choice = choice[idx]
                    if idx == 0:
                        shop_select_grid = SELECT_GRID_6X1
                    else:
                        shop_select_grid = SELECT_GRID_4X1
                    break
        elif lgroup == 'plate':
            shop_select_grid = SELECT_GRID_5X1

        if shop_select_grid is None:
            logger.warning(f'Failed to find applicable grid for group \'{lgroup}\'')
            return None

        # Return button from appropriate grid based on 'choice'
        if choice in choices:
            return shop_select_grid.buttons[choices.get(choice)]

        logger.critical(f'Missing \'{choice}\' in SELECT_{ugroup}')
        raise ScriptEnd

    def shop_buy_select_execute(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool: implicating failed to execute

        Raises:
            ScriptEnd:
        """
        # Base case - Only items with 'postfix' are allowed
        if not hasattr(item, 'postfix'):
            logger.critical('Unexpected item object; missing \'postfix\' attr')
            raise ScriptEnd

        # Retrieve appropriate globals and config values for processing
        # Stow variables for frequent usage
        ugroup = item.group.upper()
        postfix = item.postfix
        try:
            limit = globals()[f'SELECT_{ugroup}_LIMIT']
            choice = getattr(self.config, f'GuildShop_{ugroup}{postfix}')
        except:
            logger.critical('Missing either or both of the following:')
            logger.critical(f'- SELECT_{ugroup}_LIMIT (global)')
            logger.critical(f'- GuildShop_{ugroup}{postfix} (config)')
            raise ScriptEnd

        # Find the applicable grid and button within grid
        # If None, allow close and restart process
        select = self.shop_get_select(item, choice)
        if select is None:
            self.device.click(SHOP_CLICK_SAFE_AREA)  # Close secondary prompt
            return False

        # Click in intervals until plus/minus are onscreen
        click_timer = Timer(3, count=6)
        select_offset = (500, 400)
        while 1:
            if click_timer.reached():
                self.device.click(select)
                click_timer.reset()

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
