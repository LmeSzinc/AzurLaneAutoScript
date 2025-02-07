from typing import List
from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.template import Template
from module.logger import logger
from module.map_detection.utils import Points
from module.os_handler.map_event import MapEventHandler
from module.os_handler.os_status import OSStatus
from module.os_shop.selector import Selector
from module.os_shop.ui import OSShopUI, OS_SHOP_SCROLL
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
        logger.attr('Costs', f'{result}')
        return Points([(0., m.area[1]) for m in result]).group(threshold=5)

    @cached_property
    def os_shop_items(self) -> ItemGrid:
        os_shop_items = ItemGrid(
            grids=None, templates={}, amount_area=(77, 77, 96, 96),
            counter_area=(70, 167, 134, 186), price_area=(52, 132, 130, 165)
        )
        os_shop_items.load_template_folder('./assets/shop/os')
        os_shop_items.load_cost_template_folder('./assets/shop/os_cost')
        return os_shop_items

    def _get_os_shop_grid(self) -> ButtonGrid:
        """
        Returns shop grid.

        Returns:
            ButtonGris:
        """
        costs = self._get_os_shop_cost()
        row = len(costs)
        y = 0
        delta_y = 0

        if row == 1:
            y = 320 + costs[0][1] - 130
        elif row == 2:
            y = 320 + min(costs[0][1], costs[1][1]) - 130
            delta_y = abs(costs[0][1] - costs[1][1])

        return ButtonGrid(
            origin=(356, y), delta=(160, delta_y), button_shape=(98, 98), grid_shape=(5, row), name='OS_SHOP_GRID')

    def os_shop_get_items(self, shop_index=False, scroll_pos=False) -> List[Item]:
        """
        Args:
            shop_index (Integer): Additional shop index.
            scroll_pos (Float): Additional scroll position.

        Returns:
            list[Item]:
        """
        self.os_shop_items.grids = self._get_os_shop_grid()
        if self.config.SHOP_EXTRACT_TEMPLATE:
            self.os_shop_items.extract_template(self.device.image, './assets/shop/os')
        self.os_shop_items.predict(self.device.image, counter=True, shop_index=shop_index, scroll_pos=scroll_pos)
        shop_items = self.os_shop_items.items

        if len(shop_items):
            min_row = self.os_shop_items.grids[0, 0].area[1]
            row = [str(item) for item in shop_items if item.button[1] == min_row]
            logger.info(f'Shop row 1: {row}')
            row = [str(item) for item in shop_items if item.button[1] != min_row]
            logger.info(f'Shop row 2: {row}')
            return shop_items
        else:
            logger.info('No shop items found')

        return []

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
            logger.hr(f'OpsiShop scan {i}')
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
                    OS_SHOP_SCROLL.next_page(main=self, page=0.5, skip_first_screenshot=False)
                    cur_pos = OS_SHOP_SCROLL.cal_position(main=self)
                    continue
            self.device.click_record.clear()

        return items
