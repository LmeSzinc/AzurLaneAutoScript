from module.base.decorator import cached_property
from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1
from module.config.utils import get_os_reset_remain
from module.exception import GameStuckError, ScriptError
from module.logger import logger
from module.os_shop.akashi_shop import AkashiShop
from module.os_shop.assets import PORT_SUPPLY_CHECK, SHOP_BUY_CONFIRM
from module.os_shop.port_shop import PortShop
from module.os_shop.ui import OS_SHOP_SCROLL
from module.shop.assets import AMOUNT_MAX, AMOUNT_MINUS, AMOUNT_PLUS, SHOP_BUY_CONFIRM_AMOUNT, SHOP_BUY_CONFIRM as OS_SHOP_BUY_CONFIRM, SHOP_CLICK_SAFE_AREA
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
        amount_finish = False
        self.interval_clear([
            PORT_SUPPLY_CHECK, SHOP_BUY_CONFIRM_AMOUNT,
            SHOP_BUY_CONFIRM, OS_SHOP_BUY_CONFIRM, GET_ITEMS_1,
            SHOP_CLICK_SAFE_AREA
        ])

        while True:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_map_get_items(interval=3):
                self.interval_reset(PORT_SUPPLY_CHECK)
                success = True
                continue

            if self.appear_then_click(SHOP_BUY_CONFIRM, offset=(20, 20), interval=3):
                continue

            if self.appear_then_click(OS_SHOP_BUY_CONFIRM, offset=(20, 20), interval=3):
                continue

            if not amount_finish and self.appear(SHOP_BUY_CONFIRM_AMOUNT, offset=(20, 20)):
                amount_finish = self.shop_buy_amount_handler(button)
                if amount_finish:
                    self.interval_reset(SHOP_BUY_CONFIRM)
                    self.interval_reset(OS_SHOP_BUY_CONFIRM)
                continue

            if amount_finish and self.appear_then_click(SHOP_BUY_CONFIRM_AMOUNT, offset=(20, 20), interval=3):
                self.interval_reset(SHOP_BUY_CONFIRM_AMOUNT)
                continue

            if self.handle_popup_confirm('SHOP_BUY'):
                continue

            if not success and self.appear(PORT_SUPPLY_CHECK, offset=(20, 20), interval=5):
                amount_finish = False
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

    def shop_buy_amount_handler(self, item, skip_first_screenshot=True):
        """
        Handler item amount to buy.

        Args:
            item

        Raises:
            ScriptError: OCR_SHOP_AMOUNT
        """
        limit = -1
        retry = Timer(0, count=3)
        retry.start()
        while True:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            limit = OCR_SHOP_AMOUNT.ocr(self.device.image)

            if limit == 0:
                logger.warning('OCR_SHOP_AMOUNT resulted 0, retrying')
                self.device.click(SHOP_CLICK_SAFE_AREA)
                return False

            if limit > 0:
                break

            if retry.reached():
                logger.critical('OCR_SHOP_AMOUNT resulted error; '
                                'asset may be compromised')
                raise ScriptError
        retry.reset()


        currency = self.get_currency_coins(item)
        count = min(int(currency // item.price), item.count)

        if count == 1:
            return True

        coins = self.get_coins_no_limit(item)
        total_count = min(int(coins // item.price), item.count)

        set_to_max = False
        # Avg count of all items(no PurpleCoins) is 8.9, so use 10.
        if count <= 10:
            if count - 1 > total_count - count:
                set_to_max = True
            limit = count
        elif total_count - count <= 10:
            set_to_max = True
            limit = count
        elif count >= total_count >> 1:
            set_to_max = True
            limit = total_count - 10
        else:
            limit = 10

        self.interval_clear(AMOUNT_MAX)
        while set_to_max:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(AMOUNT_MAX, offset=(50, 50), interval=3):
                continue

            if OCR_SHOP_AMOUNT.ocr(self.device.image) > 1:
                break

        self.ui_ensure_index(limit, letter=OCR_SHOP_AMOUNT, prev_button=AMOUNT_MINUS, next_button=AMOUNT_PLUS,
                             skip_first_screenshot=True)
        return True

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
        self.os_shop_get_coins()
        skip_get_coins = True
        items.reverse()
        count = 0
        while len(items):
            logger.hr('OpsiShop buy', level=2)
            item = items.pop()
            if not skip_get_coins:
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
            if not self.check_item_count(_item):
                logger.warning(f'Get {_item.name} count error, skip.')
                continue
            if self.os_shop_buy_execute(_item):
                logger.info(f'Bought item: {_item.name}.')
                skip_get_coins = False
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

    @cached_property
    def yellow_coins_preserve(self):
        if self.is_cl1_enabled:
            return self.config.OS_CL1_YELLOW_COINS_PRESERVE
        else:
            return self.config.OS_NORMAL_YELLOW_COINS_PRESERVE

    def get_currency_coins(self, item):
        if item.cost == 'YellowCoins':
            if get_os_reset_remain() == 0:
                return self._shop_yellow_coins - 100
            else:
                return self._shop_yellow_coins - self.yellow_coins_preserve

        elif item.cost == 'PurpleCoins':
            if get_os_reset_remain() == 0:
                return self._shop_purple_coins
            else:
                return self._shop_purple_coins - self.config.OS_NORMAL_PURPLE_COINS_PRESERVE

    def get_coins_no_limit(self, item):
        if item.cost == 'YellowCoins':
            return self._shop_yellow_coins
        elif item.cost == 'PurpleCoins':
            return self._shop_purple_coins

    def is_coins_both_not_enough(self):
        if get_os_reset_remain() == 0:
            return False
        else:
            yellow = self._shop_yellow_coins < self._shop_purple_coins
            purple = self._shop_purple_coins < self.config.OS_NORMAL_PURPLE_COINS_PRESERVE
            return yellow and purple
