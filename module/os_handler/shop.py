from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.logger import logger
from module.ocr.ocr import Digit, DigitYuv
from module.os_handler.assets import *
from module.os_handler.map_event import MapEventHandler
from module.statistics.item import Item, ItemGrid
from module.ui.ui import UI
from module.log_res.log_res import log_res

OCR_SHOP_YELLOW_COINS = Digit(SHOP_YELLOW_COINS, letter=(239, 239, 239), threshold=160, name='OCR_SHOP_YELLOW_COINS')
OCR_SHOP_PURPLE_COINS = Digit(SHOP_PURPLE_COINS, letter=(255, 255, 255), name='OCR_SHOP_PURPLE_COINS')


class OSShopPrice(DigitYuv):
    def after_process(self, result):
        result = result.replace('I', '1').replace('D', '0').replace('S', '5')

        prev = result
        if result.startswith('0'):
            result = '1' + result
            logger.warning(f'OS shop amount {prev} is revised to {result}')

        result = super().after_process(result)
        return result


class OSShopHandler(UI, MapEventHandler):
    _shop_yellow_coins = 0
    _shop_purple_coins = 0

    def os_shop_get_coins(self):
        self._shop_yellow_coins = OCR_SHOP_YELLOW_COINS.ocr(self.device.image)
        self._shop_purple_coins = OCR_SHOP_PURPLE_COINS.ocr(self.device.image)
        log_res.log_res(self,self._shop_yellow_coins,'opcoin')
        log_res.log_res(self,self._shop_purple_coins,'purplecoin')
        logger.info(f'Yellow coins: {self._shop_yellow_coins}, purple coins: {self._shop_purple_coins}')

    @cached_property
    def os_shop_items(self):
        """
        Returns:
            ItemGrid:
        """
        shop_grid = ButtonGrid(
            origin=(237, 219), delta=(189, 224), button_shape=(98, 98), grid_shape=(4, 2), name='SHOP_GRID')
        shop_items = ItemGrid(shop_grid, templates={}, amount_area=(60, 74, 96, 95))
        shop_items.price_ocr = OSShopPrice([], letter=(255, 223, 57), threshold=32, name='Price_ocr')
        shop_items.load_template_folder('./assets/shop/os')
        shop_items.load_cost_template_folder('./assets/shop/os_cost')
        return shop_items

    def os_shop_get_items(self, name=True):
        """
        Args:
            name (bool): If detect item name. True if detect akashi shop, false if detect port shop.

        Returns:
            list[Item]:
        """
        if self.config.SHOP_EXTRACT_TEMPLATE:
            self.os_shop_items.extract_template(self.device.image, './assets/shop/os')
        self.os_shop_items.predict(self.device.image, name=name, amount=name, cost=True, price=True)

        items = self.os_shop_items.items
        if len(items):
            min_row = self.os_shop_items.grids[0, 0].area[1]
            row = [str(item) for item in items if item.button[1] == min_row]
            logger.info(f'Shop row 1: {row}')
            row = [str(item) for item in items if item.button[1] != min_row]
            logger.info(f'Shop row 2: {row}')
            return items
        else:
            logger.info('No shop items found')
            return []

    def os_shop_get_item_to_buy_in_akashi(self):
        """
        Returns:
            Item:
        """
        self.os_shop_get_coins()
        items = self.os_shop_get_items(name=True)
        # Shop supplies do not appear immediately, need to confirm if shop is empty.
        for _ in range(2):
            if not len(items):
                logger.info('Empty akashi shop, confirming')
                self.device.sleep(0.5)
                self.device.screenshot()
                items = self.os_shop_get_items(name=True)
                continue
            else:
                break

        try:
            selection = self.config.OpsiGeneral_AkashiShopFilter.replace(' ', '').replace('\n', '').split('>')
        except Exception:
            logger.warning(f'Invalid OS akashi buy filter string: {self.config.OpsiGeneral_AkashiShopFilter}')
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

    def os_shop_get_item_to_buy_in_port(self):
        """
        Returns:
            Item:
        """
        self.os_shop_get_coins()
        items = self.os_shop_get_items(name=False)

        for item in items:
            if item.cost == 'YellowCoins':
                if item.price > self._shop_yellow_coins:
                    continue
            if item.cost == 'PurpleCoins':
                if item.price > self._shop_purple_coins:
                    continue

            return item

        return None

    def os_shop_buy_execute(self, button, skip_first_screenshot=True):
        """
        Args:
            button: Item to buy
            skip_first_screenshot:

        Pages:
            in: PORT_SUPPLY_CHECK
        """
        success = False
        self.interval_clear(PORT_SUPPLY_CHECK)
        self.interval_clear(SHOP_BUY_CONFIRM)

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_map_get_items(interval=1):
                self.interval_reset(PORT_SUPPLY_CHECK)
                success = True
                continue
            if self.appear_then_click(SHOP_BUY_CONFIRM, offset=(20, 20), interval=3):
                self.interval_reset(PORT_SUPPLY_CHECK)
                continue
            if self.appear(PORT_SUPPLY_CHECK, offset=(20, 20), interval=5):
                self.device.click(button)
                continue

            # End
            if success and self.appear(PORT_SUPPLY_CHECK, offset=(20, 20)):
                break

    def os_shop_buy(self, select_func):
        """
        Args:
            select_func:

        Returns:
            int: Items bought.

        Pages:
            in: PORT_SUPPLY_CHECK
        """
        count = 0
        for _ in range(12):
            button = select_func()
            if button is None:
                logger.info('Shop buy finished')
                return count
            else:
                self.os_shop_buy_execute(button)
                count += 1
                continue

        logger.warning('Too many items to buy, stopped')
        return count

    def handle_port_supply_buy(self):
        """
        Returns:
            bool: True if success to buy any or no items found.
                False if not enough coins to buy any.

        Pages:
            in: PORT_SUPPLY_CHECK
        """
        count = self.os_shop_buy(select_func=self.os_shop_get_item_to_buy_in_port)
        return count > 0 or len(self.os_shop_items.items) == 0

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
        self.os_shop_buy(select_func=self.os_shop_get_item_to_buy_in_akashi)
        self.ui_back(appear_button=PORT_SUPPLY_CHECK, check_button=self.is_in_map, skip_first_screenshot=True)
