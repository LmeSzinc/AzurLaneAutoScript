from module.base.button import Button, ButtonGrid
from module.base.timer import Timer
from module.base.decorator import cached_property
from module.combat.assets import GET_ITEMS_1
from module.logger import logger
from module.reward.tactical_class import Book
from module.shop.assets import *
from module.statistics.item import ItemGrid
from module.ui.assets import BACK_ARROW
from module.ui.ui import UI


class ShopItemGrid(ItemGrid):
    def predict(self, image, name=True, amount=True, cost=False, price=False):
        super().predict(image, name, amount, cost, price)

        for item in self.items:
            name = item.name[0:4].lower()
            if 'book' in name:
                # Created to just not access protected variable
                # accessor returns tuple, not button itself
                btn = Button(item.button, None, item.button)

                # Cannot use match_template, use tactical_class
                # to identify exact book
                # For some shops, book may be grey thus invalid
                # but does not matter within this context
                book = Book(image, btn)
                item.name = f'{item.name[0:-2]}T{book.tier}'

        return self.items


class ShopBase(UI):
    @cached_property
    def shop_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        shop_grid = ButtonGrid(
            origin=(477, 152), delta=(156, 214), button_shape=(96, 96), grid_shape=(5, 2), name='SHOP_GRID')
        return shop_grid

    def shop_get_currency(self, key='gold_coins'):
        """
        Args:
            key: String identifies func to acquire currency
                 in wallet for shop
        """
        try:
            self.__getattribute__(f'shop_get_{key}')()
        except AttributeError:
            logger.warn(f'shop_get_currency --> Missing func shop_get_{key}')

    def shop_get_items(self, key='general'):
        """
        Args:
            key: String identifies cached_property ItemGrid

        Returns:
            list[Item]:
        """
        # Retrieve corresponding 'key' item grid
        try:
            item_grid = self.__getattribute__(f'shop_{key}_items')
        except AttributeError:
            logger.warn(f'shop_get_items --> Missing cached_property shop_{key}_items')
            return []

        item_grid.predict(self.device.image, name=True, amount=False, cost=True, price=True)

        items = item_grid.items
        if len(items):
            min_row = item_grid.grids[0, 0].area[1]
            row = [str(item) for item in items if item.button[1] == min_row]
            logger.info(f'Shop row 1: {row}')
            row = [str(item) for item in items if item.button[1] != min_row]
            logger.info(f'Shop row 2: {row}')
            return items
        else:
            logger.info('No shop items found')
            return []

    def shop_check_item(self, item, key='general'):
        """
        Args:
            item: Item to check
            key: String identifies shop_icheck_item_x

        Returns:
            Item:
        """
        try:
            return self.__getattribute__(f'shop_check_item_{key}')(item)
        except AttributeError:
            logger.warn(f'shop_check_item --> Missing func shop_check_{key}_item')
            return False

    def shop_get_item_to_buy(self, shop_type='general', currency='gold_coins', selection=''):
        """
        Args:
            shop_type: String assists with shop_get_items
            currency: String assists with shop_get_currency
            selection: String user configured value, items desired

        Returns:
            Item:
        """
        self.shop_get_currency(key=currency)
        items = self.shop_get_items(key=shop_type)

        try:
            selection = selection.replace(' ', '').split('>')
        except AttributeError:
            logger.warning('shop_get_item_to_buy --> Invalid filter string '
                           f'was provided for {shop_type}: {selection}')
            return None

        for select in selection:
            for item in items:
                if select not in item.name:
                    continue
                if not self.shop_check_item(item, key=shop_type):
                    continue

                return item

        return None

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
            if self.appear(GET_ITEMS_1, interval=1):
                self.device.click(SHOP_CLICK_SAFE_AREA)
                self.interval_reset(BACK_ARROW)
                success = True
                continue

            # End
            if success and self.appear(BACK_ARROW, offset=(20, 20)):
                break

    def shop_buy(self, shop_type='general', currency='gold_coins', selection=''):
        """
        Args:
            shop_type: String assists with shop_get_item_to_buy
            currency: String assists with shop_get_item_to_buy
            selection: String user configured value, items desired

        Returns:
            int:
        """
        count = 0
        for _ in range(12):
            item = self.shop_get_item_to_buy(shop_type, currency, selection)
            if item is None:
                logger.info('Shop buy finished')
                return count
            else:
                self.shop_buy_execute(item)
                count += 1
                continue

        logger.warning('Too many items to buy, stopped')
        return count

    def shop_refresh(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot: bool

        Returns:
            None: exits appropriately therefore successful
        """
        exit_timer = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(SHOP_REFRESH, interval=3):
                exit_timer.reset()
                continue
            if self.handle_popup_confirm('SHOP_REFRESH_CONFIRM'):
                exit_timer.reset()
                continue

            # End
            if self.appear(BACK_ARROW, offset=(20, 20)):
                if exit_timer.reached():
                    break
            else:
                exit_timer.reset()
        self.ensure_no_info_bar()
