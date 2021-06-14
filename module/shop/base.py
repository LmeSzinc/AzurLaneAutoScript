from module.base.button import Button, ButtonGrid
from module.base.decorator import cached_property
from module.logger import logger
from module.reward.tactical_class import Book
from module.statistics.item import ItemGrid
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
                # but does not matter for this method
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
        try:
            self.__getattribute__(f'shop_get_{key}')()
        except AttributeError:
            logger.warn(f'Attribute key \'{key}\' is invalid, cannot retrieve currency of shop')

    def shop_get_items(self, key='general'):
        """
        Returns:
            list[Item]:
        """
        # Retrieve corresponding 'key' item grid
        try:
            item_grid = self.__getattribute__(f'shop_{key}_items')
        except AttributeError:
            logger.warn(f'Attribute key \'{key}\' is invalid, no shop items could be retrieved')
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
