from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1, GET_SHIP
from module.logger import logger
from module.shop.assets import *
from module.shop.base_globals import *
from module.statistics.item import ItemGrid
from module.tactical.tactical_class import Book
from module.ui.assets import BACK_ARROW
from module.ui.ui import UI


class ShopItemGrid(ItemGrid):
    def predict(self, image, name=True, amount=True, cost=False, price=False, tag=False):
        """
        Overridden to iterate, corrects 'Book' type items and add additional
        attributes used to generalize identification
        """
        super().predict(image, name, amount, cost, price, tag)

        for item in self.items:
            # Every item is given a new attr 'alt_name'
            # a list of alternative / equivalent names
            # for the item in question
            item.alt_name = [item.name, item.name[:-2]]

            if item.name in ITEM_NO_TIERS:
                item.alt_name.remove(item.name[:-2])

            if 'Book' in item.name:
                # Created to just not access protected variable
                # accessor returns tuple, not button itself
                btn = Button(item.button, None, item.button)

                # Cannot use match_template, use tactical_class
                # to identify exact book
                # For some shops, book may be grey thus invalid
                # but does not matter within this context
                book = Book(image, btn)
                item.name = f'{item.name[:-2]}T{book.tier}'
                item.alt_name = ['Book', item.name, item.name[:-2], f'BookT{book.tier}']

            if 'Plate' in item.name:
                item.alt_name.extend(['Plate', f'Plate{item.name[-2:]}'])

            if 'Retrofit' in item.name:
                item.alt_name.extend(['Retrofit', f'Retrofit{item.name[-2:]}'])

            if 'PR' in item.name or 'DR' in item.name:
                item.alt_name = [
                    item.name,
                    f'{item.name[:2]}BP',
                    f'{item.name[:2]}{BP_SERIES[f"{item.name[2:-2].lower()}"]}BP',
                ]

            # Clear out duplicates in 'alt_name'
            item.alt_name = list(set(item.alt_name))
        return self.items


class ShopBase(UI):
    @cached_property
    def shop_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        shop_grid = ButtonGrid(
            origin=(477, 152), delta=(156, 214), button_shape=(96, 97), grid_shape=(5, 2), name='SHOP_GRID')
        return shop_grid

    def shop_get_currency(self, key='general'):
        """
        Args:
            key: String identifies func to acquire currency
                 for shop

        Returns:
            int:
        """
        try:
            return self.__getattribute__(f'shop_{key}_get_currency')()
        except AttributeError:
            logger.warning(f'shop_get_currency --> Missing func shop_{key}_get_currency')
            return 0

    def shop_items_loading_finished(self, items, key='medal'):
        """
        Check if shop items loading is finished. If not, the game shows some default items.

        Args:
            items: list[Item]
            key: String identifies which shop

        Returns:
            bool:
        """
        # Use default price to check
        try:
            default_price = self.__getattribute__(f'shop_{key}_default_price')
        except AttributeError:
            return True

        for item in items:
            if int(item.price) == default_price:
                return False
        return True

    def shop_get_items(self, key='general', skip_first_screenshot=True):
        """
        Args:
            key (str): String identifies cached_property ItemGrid
            skip_first_screenshot (bool):

        Returns:
            list[Item]:
        """
        # Retrieve corresponding 'key' item grid
        try:
            item_grid = self.__getattribute__(f'shop_{key}_items')
        except AttributeError:
            logger.warning(f'shop_get_items --> Missing cached_property shop_{key}_items')
            return []

        record = 0
        exit_timer = Timer(3, count=9).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            item_grid.predict(
                self.device.image,
                name=True,
                amount=False,
                cost=True if key == 'general' else False,
                price=True,
                tag=False
            )

            if exit_timer.reached():
                logger.warning('Waiting too long for items loading, assuming loaded')
                break

            # Check unloaded items, because AL loads items too slow.
            known = len([item for item in item_grid.items if item.is_known_item])
            logger.attr('Item detected', known)
            if known == 0 or known != record:
                record = known
                continue
            else:
                record = known

            # End
            if self.shop_items_loading_finished(item_grid.items, key):
                break

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
            key: String identifies shop_check_x_item

        Returns:
            bool:
        """
        try:
            return self.__getattribute__(f'shop_{key}_check_item')(item)
        except AttributeError:
            logger.warning(f'shop_check_item --> Missing func shop_{key}_check_item')
            return False

    def _is_shop_custom_item(self, item, shop_type='general'):
        """
        Buy custom items without the restriction of filter string.

        Args:
            item (Item):
            shop_type (str): String assists with shop_get_items

        Returns:
            bool:
        """
        if shop_type == 'general':
            if self.config.GeneralShop_BuySkinBox:
                if (not item.is_known_item()) and item.amount == 1 and item.cost == 'Coins' and item.price == 7000:
                    logger.info(f'Item {item} is considered to be an equip skin box')
                    try:
                        if self._shop_gold_coins > item.price:
                            return True
                    except AttributeError:
                        logger.warning('Missing _shop_gold_coins')

        return False

    def shop_get_item_to_buy(self, items, shop_type='general', selection=''):
        """
        Args:
            items list(Item): acquired from shop_get_items
            shop_type (str): assists with _is_shop_custom_item
            selection (str): user configured value, items desired

        Returns:
            Item: Item to buy, or None.
        """
        try:
            selection = selection.replace(' ', '').replace('\n', '').split('>')
            selection = list(filter(''.__ne__, selection))
        except AttributeError:
            logger.warning('shop_get_item_to_buy --> Invalid filter string '
                           f'was provided for {shop_type}: {selection}')
            return None

        for select in selection:
            # 'Choice Ship' purchases are not supported
            if 'ship' in select.lower():
                continue

            for item in items:
                if self._is_shop_custom_item(item, shop_type=shop_type):
                    return item
                if select not in item.alt_name:
                    continue
                if not self.shop_check_item(item, key=shop_type):
                    continue

                return item

        return None

    def shop_buy_execute(self, item, skip_first_screenshot=True):
        """
        Args:
            item: Item/Button to click and buy
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
            if self.appear(GET_SHIP, interval=1):
                self.device.click(SHOP_CLICK_SAFE_AREA)
                self.interval_reset(BACK_ARROW)
                continue
            if self.appear(GET_ITEMS_1, interval=1):
                self.device.click(SHOP_CLICK_SAFE_AREA)
                self.interval_reset(BACK_ARROW)
                success = True
                continue
            if self.handle_info_bar():
                self.interval_reset(BACK_ARROW)
                success = True
                continue

            # End
            if success and self.appear(BACK_ARROW, offset=(20, 20)):
                break

    def shop_buy(self, shop_type='general', selection=''):
        """
        Args:
            shop_type: String assists with shop_get_item_to_buy
            selection: String user configured value, items desired

        Returns:
            bool: If success, and able to continue.
        """
        logger.hr(f'{shop_type} shop buy', level=2)
        for _ in range(12):
            # Get first for innate delay to ocr
            # shop currency for accurate parse
            items = self.shop_get_items(key=shop_type)
            currency = self.shop_get_currency(key=shop_type)
            if currency <= 0:
                logger.warning(f'Current funds: {currency}, stopped')
                return False

            item = self.shop_get_item_to_buy(items, shop_type, selection)
            if item is None:
                logger.info('Shop buy finished')
                return True
            else:
                self.shop_buy_execute(item)
                continue

        logger.warning('Too many items to buy, stopped')
        return True
