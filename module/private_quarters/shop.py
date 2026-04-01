import re

from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.filter import Filter
from module.logger import logger
from module.private_quarters.clerk import PQShopClerk
from module.private_quarters.status import PQStatus, OCR_SHOP_PRICE
from module.statistics.item import ItemGrid

FILTER_REGEX = re.compile(
    '^(gift|furn|misc'
    ')'

    '(sirius'
    '|cake|roses'
    ')'

    '([1-9]+)?$',
    flags=re.IGNORECASE)
FILTER_ATTR = ('group', 'sub_genre', 'tier')
FILTER = Filter(FILTER_REGEX, FILTER_ATTR)


class PQShopItemGrid(ItemGrid):
    def predict(self, image, name=True, amount=True, cost=False, price=False, tag=False):
        """
        Define new attributes to predicted Item obj for shop item filtering
        """
        super().predict(image, name, amount, cost, price, tag)

        for item in self.items:
            # Set defaults
            item.group, item.sub_genre, item.tier = None, None, None

            # Can use regular expression to quickly populate
            # the new attributes
            name = item.name
            result = re.search(FILTER_REGEX, name)
            if result:
                item.group, item.sub_genre, item.tier = \
                    [group.lower()
                     if group is not None else None
                     for group in result.groups()]
            else:
                # if not name.isnumeric():
                #     logger.warning(f'Unable to parse shop item {name}; '
                #                     'check template asset and filter regexp')
                #     raise ScriptError
                continue

        return self.items


class PQShop(PQShopClerk, PQStatus):
    gems = 0
    shop_template_folder = './assets/shop/private_quarters'

    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        list_filter = []
        if self.config.PrivateQuarters_BuyRoses:
            list_filter.append('GiftRoses')
        if self.config.PrivateQuarters_BuyCake:
            list_filter.append('GiftCake')

        return ' > '.join(list_filter).strip()

    @cached_property
    def shop_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        shop_grid = ButtonGrid(
            origin=(290, 215), delta=(230, 0), button_shape=(96, 96), grid_shape=(4, 1),
            name='PRIVATE_QUARTERS_BUTTON_GRID_ITEM')
        return shop_grid

    @cached_property
    def shop_private_quarters_items(self):
        """
        Returns:
            PQShopItemGrid:
            cost_area=(-52, 330, -26, 353)
        """
        shop_grid = self.shop_grid
        shop_private_quarters_items = PQShopItemGrid(shop_grid, templates={},
                                                     cost_area=(-52, 330, -26, 353), price_area=(-26, 331, 36, 357))
        shop_private_quarters_items.price_ocr = OCR_SHOP_PRICE
        shop_private_quarters_items.load_template_folder(self.shop_template_folder)
        shop_private_quarters_items.load_cost_template_folder('./assets/shop/private_quarters_cost')
        return shop_private_quarters_items

    def shop_items(self):
        """
        Shared alias for all shops
        If there are server-lang
        differences, reference
        shop_guild/medal for @Config
        example

        Returns:
            ShopItemGrid:
        """
        return self.shop_private_quarters_items

    def shop_currency(self):
        """
        Ocr shop guild currency if needed
        (gold coins and gems)
        Then return gold coin count

        Returns:
            int: gold coin amount
        """
        self._currency = self.status_get_gold_coins()
        self.gems = self.status_get_gems()
        logger.info(f'Gold coins: {self._currency}, Gems: {self.gems}')

    def shop_check_item(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool: whether item can be bought
        """
        if self.config.PrivateQuarters_BuyRoses:
            if item.sub_genre == 'roses':
                if 24000 > self._currency:
                    return False
                return True

        if self.config.PrivateQuarters_BuyCake:
            if item.sub_genre == 'cake':
                if 210 > self.gems:
                    return False
                return True

        return False

    def shop_get_item_to_buy(self, items):
        """
        Args:
            items list(Item): acquired from shop_get_items

        Returns:
            Item: Item to buy, or None.
        """
        # Load selection, apply filter,
        # and return 1st item in result if any
        FILTER.load(self.shop_filter)
        filtered = FILTER.apply(items, self.shop_check_item)

        if not filtered:
            return None
        logger.attr('Item_sort', ' > '.join([str(item) for item in filtered]))

        return filtered[0]
