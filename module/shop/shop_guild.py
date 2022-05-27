import cv2

from module.base.decorator import Config, cached_property
from module.base.timer import Timer
from module.exception import ScriptError
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from module.shop.assets import *
from module.shop.base import ShopBase, ShopItemGrid
from module.shop.shop_guild_globals import *
from module.shop.ui import ShopUI


class StockCounter(DigitCounter):
    def pre_process(self, image):
        # Convert to gray scale
        r, g, b = cv2.split(image)
        image = cv2.max(cv2.max(r, g), b)

        return 255 - image


SHOP_SELECT_PR = [SHOP_SELECT_PR1, SHOP_SELECT_PR2, SHOP_SELECT_PR3]

OCR_SHOP_GUILD_COINS = Digit(SHOP_GUILD_COINS, letter=(255, 255, 255), name='OCR_SHOP_GUILD_COINS')
OCR_SHOP_SELECT_STOCK = StockCounter(SHOP_SELECT_STOCK)


class GuildShop(ShopBase, ShopUI):
    _shop_guild_coins = 0

    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return self.config.GuildShop_Filter.strip()

    @cached_property
    @Config.when(SERVER='cn')
    def shop_guild_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_guild_items = ShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_guild_items.load_template_folder('./assets/shop/guild_cn')
        shop_guild_items.load_cost_template_folder('./assets/shop/cost')
        return shop_guild_items

    @cached_property
    @Config.when(SERVER='tw')
    def shop_guild_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_guild_items = ShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_guild_items.load_template_folder('./assets/shop/guild_cn')
        shop_guild_items.load_cost_template_folder('./assets/shop/cost')
        return shop_guild_items

    @cached_property
    @Config.when(SERVER=None)
    def shop_guild_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_guild_items = ShopItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_guild_items.load_template_folder('./assets/shop/guild')
        shop_guild_items.load_cost_template_folder('./assets/shop/cost')
        return shop_guild_items

    def shop_items(self):
        """
        Shared alias for all shops,
        so for @Config must define
        a unique alias as cover

        Returns:
            ShopItemGrid:
        """
        return self.shop_guild_items

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

    def shop_get_choice(self, item):
        """
        Gets the configuration saved in
        GuildShop_X for item

        Args:
            item (Item):

        Returns:
            str

        Raises:
            ScriptError
        """
        group = item.group
        if group == 'pr':
            postfix = None
            for _ in range(3):
                if _:
                    self.device.sleep((0.3, 0.5))
                    self.device.screenshot()

                for idx, btn in enumerate(SHOP_SELECT_PR):
                    if self.appear(btn, offset=(20, 20)):
                        postfix = f'{idx + 1}'
                        break

                if postfix is not None:
                    break
                logger.warning('Failed to detect PR series, '
                               'app may be lagging or frozen')
        else:
            postfix = f'_{item.tier.upper()}'

        ugroup = group.upper()
        try:
            return getattr(self.config, f'GuildShop_{ugroup}{postfix}')
        except:
            logger.critical(f'No configuration with name '
                            f'\'GuildShop_{ugroup}{postfix}\'')
            raise ScriptError

    def shop_get_select(self, item):
        """
        Gets the appropriate select
        grid button

        Args:
            item (Item):

        Returns:
            Button

        Raises:
            ScriptError
        """
        # Item group must belong in SELECT_ITEM_INFO_MAP
        group = item.group
        if group not in SELECT_ITEM_INFO_MAP:
            logger.critical(f'Unexpected item group \'{group}\'; '
                            f'expected one of {SELECT_ITEM_INFO_MAP.keys()}')
            raise ScriptError

        # Get configured choice for item
        choice = self.shop_get_choice(item)

        # Get appropriate select button for click
        try:
            item_info = SELECT_ITEM_INFO_MAP[group]
            index = item_info['choices'][choice]
            if group == 'pr':
                for idx, btn in enumerate(SHOP_SELECT_PR):
                    if self.appear(btn, offset=(20, 20)):
                        series_key = f's{idx + 1}'
                        return item_info['grid'][series_key].buttons[index]
            else:
                return item_info['grid'].buttons[index]
        except:
            logger.critical(f'SELECT_ITEM_INFO_MAP may be malformed; '
                            f'item group \'{group}\' entry is compromised')
            raise ScriptError

    def shop_buy_select_execute(self, item):
        """
        Args:
            item (Item):

        Returns:
            bool:
        """
        # Search for appropriate select grid button for item
        # If None, allow close and restart process
        select = self.shop_get_select(item)

        # Game bug; stock limit on screen may differ from
        # known wiki values so read first, fallback if fail
        _, _, limit = OCR_SHOP_SELECT_STOCK.ocr(self.device.image)
        if not limit:
            logger.info('Unable to read current stock; fallback to dictionary')
            limit = SELECT_ITEM_INFO_MAP[item.group]['limit']

        # Click in intervals until plus/minus are onscreen
        click_timer = Timer(3, count=6)
        select_offset = (500, 400)
        while 1:
            if click_timer.reached():
                self.device.click(select)
                click_timer.reset()

            # Scan for plus/minus locations; searching within
            # offset will update the click posiion automatically
            self.device.screenshot()
            if self.appear(SELECT_MINUS, offset=select_offset) and self.appear(SELECT_PLUS, offset=select_offset):
                break
            else:
                continue

        # Total number to purchase altogether
        total = int(self._shop_guild_coins // item.price)
        diff = limit - total
        if diff > 0:
            limit = total

        # Alias OCR_SHOP_SELECT_STOCK to adapt with
        # ui_ensure_index; prevent overbuying when
        # out of stock; item.price may still evaluate
        # incorrectly
        def shop_buy_select_ensure_index(image):
            current, remain, _ = OCR_SHOP_SELECT_STOCK.ocr(image)
            if not current:
                group_case = item.group.title() if len(item.group) > 2 else item.group.upper()
                logger.info(f'{group_case}(s) out of stock; exit to prevent overbuying')
                return limit
            return remain

        self.ui_ensure_index(limit, letter=shop_buy_select_ensure_index, prev_button=SELECT_MINUS, next_button=SELECT_PLUS,
                             skip_first_screenshot=True)
        self.device.click(SHOP_BUY_CONFIRM_SELECT)
        return True

    def shop_interval_clear(self):
        """
        Clear interval on select assets for
        shop_buy_handle
        """
        super().shop_interval_clear()
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
            self.shop_buy_select_execute(item)
            self.interval_reset(SHOP_BUY_CONFIRM_SELECT)
            return True

        return False

    def run(self):
        """
        Run Guild Shop
        """
        # Base case; exit run if filter empty
        if not self.shop_filter:
            return

        # When called, expected to be in
        # correct Guild Shop interface
        logger.hr('Guild Shop', level=1)

        # Execute buy operations
        # Refresh if enabled and available
        refresh = self.config.GuildShop_Refresh
        for _ in range(2):
            success = self.shop_buy()
            if not success:
                break
            if refresh:
                # Refresh costs 50 and PlateT4 costs 60
                if self._shop_guild_coins >= 110:
                    if self.shop_refresh():
                        continue
                else:
                    logger.info('Guild coins < 110, skip refreshing')
            break
