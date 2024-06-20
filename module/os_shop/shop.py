from module.config.utils import get_os_reset_remain
from module.exception import ScriptError
from module.logger import logger
from module.os_shop.assets import PORT_SUPPLY_CHECK, SHOP_BUY_CONFIRM
from module.os_shop.akashi_shop import AkashiShop
from module.os_shop.port_shop import PortShop
from module.os_shop.ui import OS_SHOP_SCROLL
from module.shop.assets import AMOUNT_MAX, AMOUNT_MINUS, AMOUNT_PLUS, SHOP_BUY_CONFIRM_AMOUNT, SHOP_BUY_CONFIRM as OS_SHOP_BUY_CONFIRM
from module.shop.clerk import OCR_SHOP_AMOUNT


class OSShop(PortShop, AkashiShop):
    def os_shop_buy_execute(self, button, skip_first_screenshot=True) -> bool:
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
        self.interval_clear(SHOP_BUY_CONFIRM_AMOUNT)
        self.interval_clear(OS_SHOP_BUY_CONFIRM)

        while True:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_map_get_items(interval=1):
                self.interval_reset(PORT_SUPPLY_CHECK)
                success = True
                continue

            if self.appear_then_click(SHOP_BUY_CONFIRM, offset=(20, 20), interval=1):
                self.interval_reset(SHOP_BUY_CONFIRM)
                continue

            if self.appear_then_click(OS_SHOP_BUY_CONFIRM, offset=(20, 20), interval=1):
                self.interval_reset(OS_SHOP_BUY_CONFIRM)
                continue

            if self.appear(SHOP_BUY_CONFIRM_AMOUNT, offset=(20, 20), interval=1):
                self.shop_buy_amount_handler(button)
                self.device.click(SHOP_BUY_CONFIRM_AMOUNT)
                self.interval_reset(SHOP_BUY_CONFIRM_AMOUNT)
                continue

            if not success and self.appear(PORT_SUPPLY_CHECK, offset=(20, 20), interval=5):
                self.device.click(button)
                continue

            # End
            if success and self.appear(PORT_SUPPLY_CHECK, offset=(20, 20)):
                break

        return success

    def os_shop_buy(self, select_func) -> int:
        """
        Args:
            select_func:
        @@ -213,20 +341,131 @@ def os_shop_buy(self, select_func):
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

    def shop_buy_amount_handler(self, item):
        """
        Handler item amount to buy.

        Args:
            item

        Raises:
            ScriptError: OCR_SHOP_AMOUNT
        """
        currency = self.get_currency_coins(item)

        total = int(currency // item.price)

        if total == 1:
            return

        limit = 0
        for _ in range(3):
            self.appear_then_click(AMOUNT_MAX, offset=(50, 50))
            self.device.sleep((0.3, 0.5))
            self.device.screenshot()
            limit = OCR_SHOP_AMOUNT.ocr(self.device.image)
            if limit and limit > 1:
                break

        if not limit:
            logger.critical('OCR_SHOP_AMOUNT resulted in zero (0); '
                            'asset may be compromised')
            raise ScriptError

        diff = limit - total
        if diff > 0:
            limit = total

        self.ui_ensure_index(limit, letter=OCR_SHOP_AMOUNT, prev_button=AMOUNT_MINUS, next_button=AMOUNT_PLUS,
                             skip_first_screenshot=True)

    def handle_port_supply_buy(self) -> bool:
        """
        Returns:
            bool: True if success to buy any or no items found.
                False if not enough coins to buy any.

        Pages:
            in: PORT_SUPPLY_CHECK
        """
        items = self.scan_all()
        if not len(items):
            logger.warning('Empty OS shop.')
            return False
        items = self.items_filter_in_os_shop(items)
        if not len(items):
            logger.warning('Nothing to buy.')
            return False
        items.reverse()
        count = 0
        while len(items):
            item = items.pop()
            self.os_shop_get_coins()
            if item.price > self.get_currency_coins(item):
                logger.info(f'Not enough coins to buy item: {item.name}, skip.')
                if self.is_coins_both_not_enough():
                    logger.info('Not enough coins to buy any items, stop.')
                    break
                continue
            logger.info(f'Buying item: {item.name}. In shop {item.shop_index + 1}. At pos {item.scroll_pos:.2f}.')
            self.os_shop_side_navbar_ensure(upper=item.shop_index + 1)
            OS_SHOP_SCROLL.set(item.scroll_pos, main=self, skip_first_screenshot=False)
            _item = self.os_shop_get_items_to_buy(name=item.name, price=item.price)
            if _item is None:
                logger.warning(f'Item {item.name} not found in shop {item.shop_index + 1} at pos {item.scroll_pos:.2f}, skip.')
                continue
            if self.os_shop_buy_execute(_item):
                logger.info(f'Bought item: {_item.name}.')
                count += 1
            self.device.click_record.clear()
        logger.info(f'Bought {f"{count} items" if count else "nothing"} in port.')
        return True

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

    def get_currency_coins(self, item):
        if item.cost == 'YellowCoins':
            if get_os_reset_remain() == 0:
                return self._shop_yellow_coins
            elif self.is_cl1_enabled:
                return self._shop_yellow_coins - self.config.OS_CL1_YELLOW_COINS_PRESERVE
            else:
                return self._shop_yellow_coins - self.config.OS_NORMAL_YELLOW_COINS_PRESERVE

        elif item.cost == 'PurpleCoins':
            if get_os_reset_remain() == 0:
                return self._shop_purple_coins
            else:
                return self._shop_purple_coins - self.config.OS_NORMAL_PURPLE_COINS_PRESERVE

    def is_coins_both_not_enough(self):
        if get_os_reset_remain() == 0:
            return False
        else:
            if self.is_cl1_enabled:
                yellow = self._shop_yellow_coins < self.config.OS_CL1_YELLOW_COINS_PRESERVE
            else:
                yellow = self._shop_yellow_coins < self.config.OS_NORMAL_YELLOW_COINS_PRESERVE
            purple = self._shop_purple_coins < self.config.OS_NORMAL_PURPLE_COINS_PRESERVE
            return yellow and purple
