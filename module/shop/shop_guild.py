from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import area_offset, get_color
from module.combat.assets import GET_ITEMS_1
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.shop.base import ShopBase, ShopItemGrid
from module.shop.shop_guild_globals import *
from module.ui.assets import BACK_ARROW

OCR_SHOP_GUILD_COINS = Digit(SHOP_GUILD_COINS, letter=(255, 255, 255), name='OCR_SHOP_GUILD_COINS')
OCR_SHOP_SELECT_TOTAL_PRICE = Digit(SHOP_SELECT_TOTAL_PRICE, letter=(255, 255, 255), name='OCR_SHOP_SELECT_TOTAL_PRICE')


class GuildItemGrid(ShopItemGrid):
    def predict(self, image, name=True, amount=True, cost=False, price=False):
        super().predict(image, name, amount, cost, price)

        # Loop again, to add 'secondary_grid' attr
        # only applicable to GuildShop items
        for item in self.items:
            name = item.name[:-2].lower()
            if name in SELECT_ITEMS:
                item.secondary_grid = name
            else:
                item.secondary_grid = None

        return self.items


class GuildShop(ShopBase):
    _shop_guild_coins = 0

    def shop_get_guild_currency(self):
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

    def shop_get_select(self, category='none', choice='none'):
        """
        Args:
            category: String identifies SELECT combination
            choice: String identifies index within SELECT combination

        Returns:
            Button:
        """
        # Ensure there is valid SELECT combination according to category
        try:
            choices = globals()[f'SELECT_{category.upper()}']
        except KeyError:
            logger.warn(f'shop_get_select --> Missing SELECT_{category.upper()}')
            return None

        # Retrieve the correct SELECT_GRID based on category
        if category == 'book':
            shop_select_grid = SELECT_GRID_3X1
        elif category == 'box' or \
                category == 'retrofit' or \
                (category == 'pr' and
                 (self.appear(SHOP_SELECT_PR2) or self.appear(SHOP_SELECT_PR3))):
            shop_select_grid = SELECT_GRID_4X1
        elif category == 'pr' and self.appear(SHOP_SELECT_PR1):
            shop_select_grid = SELECT_GRID_6X1
        else:
            shop_select_grid = SELECT_GRID_5X1

        # Utilize known fixed location for correct item
        if choice in choices:
            return shop_select_grid.buttons()[choices.get(choice)]

        logger.warn(f'shop_get_select --> Missing \'{choice}\' in SELECT_{category.upper()}')
        return None

    def shop_buy_select_execute(self, item):
        """
        Args:
            item: Item to check

        Returns:
            None: implicating failed to execute
        """
        # Base Case - Must have 'secondary_grid' attr and must not be None
        if not hasattr(item, 'secondary_grid') or item.secondary_grid is None:
            logger.warn('shop_buy_select_execute --> Detected secondary '
                        'prompt but item not classified of having this option')
            self.device.click(SHOP_CLICK_SAFE_AREA)  # Close secondary prompt
            return None

        # Proceed and verify required components can be acquired
        category = item.secondary_grid
        try:
            limit = globals()[f'SELECT_{category.upper()}_LIMIT']
            choice = getattr(self.config, f'SHOP_GUILD_{category.upper()}')
        except KeyError:
            logger.warn(f'shop_buy_select_execute --> Missing SELECT_{category.upper()}_LIMIT')
            self.device.click(SHOP_CLICK_SAFE_AREA)  # Close secondary prompt
            return None
        except AttributeError:
            logger.warn(f'shop_buy_select_execute --> Missing Config SHOP_GUILD_{category.upper()}')
            self.device.click(SHOP_CLICK_SAFE_AREA)  # Close secondary prompt
            return None

        # Find and click appropriate button within secondary grid
        # This results in plus/minus appearing, click until those appear
        select = self.shop_get_select(category, choice)
        click_timer = Timer(3, count=6)
        while 1:
            if select is not None:
                if click_timer.reached():
                    self.device.click(select)
                    click_timer.reset()
            else:
                self.device.click(SHOP_CLICK_SAFE_AREA)  # Close secondary prompt
                return None

            # Scan for plus/minus locations varies based on grid and item selected
            self.device.screenshot()
            sim0, point0 = TEMPLATE_PLUS.match_result(self.device.image)
            sim1, point1 = TEMPLATE_MINUS.match_result(self.device.image)
            if sim0 < 0.85 or sim1 < 0.85:
                continue

            for index, name in enumerate(['PLUS', 'MINUS']):
                button = area_offset(area=(-12, -12, 44, 32), offset=locals()[f'point{index}'])
                color = get_color(self.device.image, button)
                locals()[name] = Button(area=button, color=color, button=button, name=f'{name}')

            break

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

        self.ui_ensure_index(limit, letter=total_price_to_count, prev_button=locals()['MINUS'],
                             next_button=locals()['PLUS'], skip_first_screenshot=True)
        self.device.click(SHOP_BUY_CONFIRM_SELECT)

    def shop_buy_execute(self, item, skip_first_screenshot=True):
        """
        Args:
            item: Item to click and buy
            skip_first_screenshot: bool

        Returns:
            None: exits appropriately therefore successful
        """
        success = False
        self.interval_clear(BACK_ARROW)
        self.interval_clear(SHOP_BUY_CONFIRM)
        self.interval_clear(SHOP_SELECT_CHECK)

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(BACK_ARROW, offset=(20, 20), interval=3):
                self.device.click(item)
                continue
            if self.appear_then_click(SHOP_BUY_CONFIRM, offset=(20, 20), interval=3):
                self.interval_reset(BACK_ARROW)
                continue
            if self.appear(SHOP_SELECT_CHECK, interval=3):
                self.shop_buy_select_execute(item)
                self.interval_reset(BACK_ARROW)
                self.interval_reset(SHOP_SELECT_CHECK)
                continue
            if self.appear(GET_ITEMS_1, interval=1):
                self.device.click(SHOP_CLICK_SAFE_AREA)
                self.interval_reset(BACK_ARROW)
                success = True
                continue
            if self.info_bar_count():
                self.ensure_no_info_bar()
                self.interval_reset(BACK_ARROW)
                success = True
                continue

            # End
            if success and self.appear(BACK_ARROW, offset=(20, 20)):
                break

    def shop_check_item_guild(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool:
        """
        if item.cost == 'GuildCoins':
            if item.price > self._shop_guild_coins:
                return False
            return True
        return False
