from typing import List
from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.template import Template
from module.logger import logger
from module.map_detection.utils import Points
from module.os_handler.map_event import MapEventHandler
from module.os_handler.os_status import OSStatus
from module.os_shop.selector import Selector
from module.os_shop.ui import OSShopPrice, OSShopUI, OS_SHOP_SCROLL
from module.os_shop.item import OSShopItem as Item, OSShopItemGrid as ItemGrid
from module.statistics.utils import load_folder


class PortShop(OSStatus, OSShopUI, Selector, MapEventHandler):
    @cached_property
    def TEMPLATES(self) -> List[Template]:
        TEMPLATES = []
        coins = load_folder('./assets/shop/os_cost')
        coins_sold_out = load_folder('./assets/shop/os_cost_sold_out')
        for c in coins.values():
            TEMPLATES.append(Template(c))
        for c in coins_sold_out.values():
            TEMPLATES.append(Template(c))
        return TEMPLATES

    def _get_os_shop_cost(self) -> list:
        """
        Returns the coordinates of the upper left corner of each coin icon.

        Returns:
            list:
        """
        image = self.image_crop((360, 320, 410, 700))
        result = sum([template.match_multi(image) for template in self.TEMPLATES], [])
        logger.info(f'Costs: {result}')
        return Points([(0., m.area[1]) for m in result]).group(threshold=5)

    @cached_property
    def os_shop_items(self) -> ItemGrid:
        os_shop_items = ItemGrid(
            grids=None, templates={}, amount_area=(77, 77, 96, 96), price_area=(52, 132, 130, 165))
        os_shop_items.price_ocr = OSShopPrice([], letter=(255, 223, 57), threshold=32, name='Price_ocr')
        os_shop_items.load_template_folder('./assets/shop/os')
        os_shop_items.load_cost_template_folder('./assets/shop/os_cost')
        return os_shop_items

    def _get_os_shop_grid(self, cost) -> ButtonGrid:
        """
        Returns shop grid.

        Args:
            cost: The coordinates of the upper left corner of coin icon.

        Returns:
            ButtonGris:
        """
        y = 320 + cost[1] - 130

        return ButtonGrid(
            origin=(356, y), delta=(160, 0), button_shape=(98, 98), grid_shape=(5, 1), name='OS_SHOP_GRID')

    def os_shop_get_items(self, shop_index=False, scroll_pos=False) -> List[Item]:
        """
        Args:
            shop_index (Integer): Additional shop index.
            scroll_pos (Float): Additional scroll position.

        Returns:
            list[Item]:
        """
        items = []
        costs = self._get_os_shop_cost()

        for cost in costs:
            self.os_shop_items.grids = self._get_os_shop_grid(cost)
            if self.config.SHOP_EXTRACT_TEMPLATE:
                self.os_shop_items.extract_template(self.device.image, './assets/shop/os')
            self.os_shop_items.predict(self.device.image, shop_index=shop_index, scroll_pos=scroll_pos)
            shop_items = self.os_shop_items.items

            if len(shop_items):
                row = [str(item) for item in shop_items]
                logger.info(f'Shop items found: {row}')
                items += shop_items
            else:
                logger.info('No shop items found')

        return items

    def os_shop_get_items_to_buy(self, name, price) -> Item:
        """
        Args:
            name (str): Item name.
            price (int): Item price.

        Returns:
            Item:
        """
        items = self.os_shop_get_items()
        for _ in range(2):
            if not len(items) or any(not item.is_known_item() for item in items):
                logger.warning('Empty OS shop or empty items, confirming')
                self.device.sleep((0.3, 0.5))
                self.device.screenshot()
                items = self.os_shop_get_items()
                continue
            else:
                _items = [item for item in items if item.name == name and item.price == price]
                if len(_items):
                    return _items.pop()

        return None

    def scan_all(self) -> List[Item]:
        """
        Returns:
            list[Item]:
        """
        items = []
        self.device.click_record.clear()

        for i in range(4):
            self.os_shop_side_navbar_ensure(upper=i + 1)
            pre_pos, cur_pos = self.init_slider()

            while True:
                pre_pos = self.pre_scroll(pre_pos, cur_pos)
                _items = self.os_shop_get_items(i, cur_pos)

                for _ in range(2):
                    if not len(_items) or any(not item.is_known_item() for item in _items):
                        logger.warning('Empty OS shop or empty items, confirming')
                        self.device.sleep((0.3, 0.5))
                        self.device.screenshot()
                        _items = self.os_shop_get_items(i, cur_pos)
                        continue
                    else:
                        items += _items
                        logger.info(f'Found {len(_items)} items in shop {i + 1} at pos {cur_pos:.2f}')
                        break

                if OS_SHOP_SCROLL.at_bottom(main=self):
                    logger.info('OS shop reach bottom, stop')
                    break
                else:
                    OS_SHOP_SCROLL.next_page(main=self, page=0.5)
                    cur_pos = OS_SHOP_SCROLL.cal_position(main=self)
                    continue
            self.device.click_record.clear()

        return items
