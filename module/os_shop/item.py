from typing import List
from module.logger import logger
from module.statistics.item import Item, ItemGrid


class OSShopItem(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shop_index = None
        self._scroll_pos = None

    @property
    def shop_index(self):
        return self._shop_index

    @shop_index.setter
    def shop_index(self, value):
        self._shop_index = value

    @property
    def scroll_pos(self):
        return self._scroll_pos

    @scroll_pos.setter
    def scroll_pos(self, value):
        self._scroll_pos = value

    def is_known_item(self) -> bool:
        if self.name == 'DefaultItem':
            return False
        elif 'Empty' in self.name:
            return False
        elif self.name.isdigit():
            return False
        else:
            return True

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((self.name, self.price, self.cost, self.shop_index, self.scroll_pos))


class OSShopItemGrid(ItemGrid):
    item_class = OSShopItem

    def predict(self, image, shop_index=None, scroll_pos=None) -> List[OSShopItem]:
        """
        Args:
            image (np.ndarray):
            shop_index (bool): If predict shop index.
            scroll_pos (bool): If predict scroll position.

        Returns:
            list[Item]:
        """
        self._load_image(image)
        amount_list = [item.crop(self.amount_area) for item in self.items]
        amount_list = self.amount_ocr.ocr(amount_list, direct_ocr=True)
        name_list = [self.match_template(item.image) for item in self.items]
        cost_list = [self.match_cost_template(item) for item in self.items]
        price_list = [item.crop(self.price_area) for item in self.items]
        price_list = self.price_ocr.ocr(price_list, direct_ocr=True)
        ignore = 0
        items = []

        for i, a, n, c, p in zip(self.items, amount_list, name_list, cost_list, price_list):
            if (p <= 0):
                ignore += 1
                continue
            i.amount = a
            i.name = n
            i.cost = c
            i.price = p
            if isinstance(shop_index, int):
                i.shop_index = shop_index
            if isinstance(scroll_pos, float):
                i.scroll_pos = scroll_pos
            items.append(i)

        if ignore > 0:
            logger.warning(f'Ignore {ignore} items, because price <= 0')

        return items
