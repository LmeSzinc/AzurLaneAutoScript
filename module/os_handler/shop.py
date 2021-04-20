from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.utils import *
from module.logger import logger
from module.ocr.ocr import Digit
from module.os_handler.assets import *
from module.os_handler.map_event import MapEventHandler
from module.statistics.item import ItemGrid, Item
from module.ui.ui import UI

OCR_SHOP_YELLOW_COINS = Digit(SHOP_YELLOW_COINS, letter=(239, 239, 239), name='OCR_SHOP_YELLOW_COINS')
OCR_SHOP_PURPLE_COINS = Digit(SHOP_PURPLE_COINS, letter=(255, 255, 255), name='OCR_SHOP_PURPLE_COINS')


class ShopHandler(UI, MapEventHandler):
    _shop_yellow_coins = 0
    _shop_purple_coins = 0

    def shop_get_coins(self):
        self._shop_yellow_coins = OCR_SHOP_YELLOW_COINS.ocr(self.device.image)
        self._shop_purple_coins = OCR_SHOP_PURPLE_COINS.ocr(self.device.image)
        logger.info(f'Yellow coins: {self._shop_yellow_coins}, purple coins: {self._shop_purple_coins}')

    @cached_property
    def shop_items(self):
        """
        Returns:
            ItemGrid:
        """
        shop_grid = ButtonGrid(
            origin=(237, 219), delta=(189, 224), button_shape=(98, 98), grid_shape=(4, 2), name='SHOP_GRID')
        shop_items = ItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_items.load_template_folder('./assets/os_shop')
        shop_items.load_cost_template_folder('./assets/os_shop_cost')
        return shop_items

    def shop_get_items(self, name=True):
        """
        Args:
            name (bool): If detect item name. True if detect akashi shop, false if detect port shop.

        Returns:
            list[Item]:
        """

        def item_name(item):
            if name:
                return f'{item.name}_x{item.amount}_{item.cost}_x{item.price}'
            else:
                return f'{item.cost}_x{item.price}'

        self.shop_items.predict(self.device.image, name=name, amount=name, cost=True, price=True)

        items = self.shop_items.items
        if len(items):
            min_row = np.min([item.button[1] for item in items])
            row = [item_name(item) for item in items if item.button[1] == min_row]
            logger.info(f'Shop row 1: {row}')
            row = [item_name(item) for item in items if item.button[1] != min_row]
            logger.info(f'Shop row 2: {row}')
            return items
        else:
            logger.info('No shop items found')
            return []

    def shop_get_item_to_buy_in_akashi(self):
        """
        Returns:
            Item:
        """
        self.shop_get_coins()
        items = self.shop_get_items(name=True)
        try:
            selection = self.config.OS_ASKSHI_SHOP_PRIORITY.replace(' ', '').split('>')
        except Exception:
            logger.warning(f'Invalid OS akashi buy filter string: {self.config.OS_ASKSHI_SHOP_PRIORITY}')
            return None

        for select in selection:
            for item in items:
                if select not in item.name:
                    continue
                if item.cost == 'YellowCoins':
                    if item.price > self._shop_yellow_coins:
                        continue
                if item.cost == 'PurpleCoins':
                    if item.price > self._shop_purple_coins:
                        continue

                return item

        return None

    def shop_get_item_to_buy_in_port(self):
        """
        Returns:
            Item:
        """
        self.shop_get_coins()
        items = self.shop_get_items(name=False)

        for item in items:
            if item.cost == 'YellowCoins':
                if item.price > self._shop_yellow_coins:
                    continue
            if item.cost == 'PurpleCoins':
                if item.price > self._shop_purple_coins:
                    continue

            return item

        return None

    def shop_buy(self, select_func, skip_first_screenshot=True):
        """
        Args:
            select_func:
            skip_first_screenshot:

        Returns:
            int: Items bought.

        Pages:
            in: PORT_SUPPLY_CHECK
        """
        count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(PORT_SUPPLY_CHECK, offset=(20, 20), interval=0.5):
                button = select_func()
                if button is None:
                    break
                else:
                    self.device.click(button)
                    count += 1
                    continue

            if self.handle_map_get_items(interval=0.5):
                self.interval_reset(PORT_SUPPLY_CHECK)
                continue
            if self.appear_then_click(SHOP_BUY_CONFIRM, offset=(20, 20), interval=0.5):
                self.interval_reset(PORT_SUPPLY_CHECK)
                continue

        return count

    def handle_port_supply_buy(self):
        """
        Returns:
            bool: True if success to buy any or no items found.
                False if not enough coins to buy any.

        Pages:
            in: PORT_SUPPLY_CHECK
        """
        count = self.shop_buy(select_func=self.shop_get_item_to_buy_in_port)
        return count > 0 or len(self.shop_items.items) == 0

    def handle_akashi_supply_buy(self, grid):
        """
        Args:
            grid: Grid where akashi stands.

        Pages:
            in: is_in_map
            out: is_in_map
        """
        self.ui_click(grid, appear_button=self.is_in_map, check_button=PORT_SUPPLY_CHECK,
                      additional=self.handle_story_skip, skip_first_screenshot=True)
        self.shop_buy(select_func=self.shop_get_item_to_buy_in_akashi)
        self.ui_back(appear_button=PORT_SUPPLY_CHECK, check_button=self.is_in_map, skip_first_screenshot=True)
