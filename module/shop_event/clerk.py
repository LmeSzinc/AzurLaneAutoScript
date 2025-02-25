import cv2
import os

from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.template import Template
from module.base.utils import save_image, load_image
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_3, GET_SHIP
from module.shop_event.item import EventShopItemGrid
from module.shop_event.ui import EventShopUI, EVENT_SHOP_SCROLL, OCR_EVENT_SHOP_ITEM_REMAIN
from module.map_detection.utils import Points
from module.logger import logger
from module.shop.assets import AMOUNT_MAX, AMOUNT_MINUS, AMOUNT_PLUS, SHOP_BUY_CONFIRM, SHOP_BUY_CONFIRM_AMOUNT, SHOP_CLICK_SAFE_AREA
from module.shop.clerk import OCR_SHOP_AMOUNT
from module.ui.assets import BACK_ARROW


class EventShopClerk(EventShopUI):
    """
    Class for Event Shop operations containing UI and items.
    """

    def record_event_shop_cost(self):
        """
        Record event pt icon for itemgrid detection.
        Uses pt icon on the upper-right part for templates.
        """
        logger.hr('Record Event Pt Icon', level=2)
        if self.event_shop_is_commission:
            save_image(load_image('./assets/shop/event_cost/CommissionPt.png'), './assets/shop/event_cost/Pt.png')
            return

        os.makedirs(os.path.dirname('./assets/shop/event_cost/'), exist_ok=True)
        scaling = 5/6
        pt_ssr_icon = self.image_crop((1036, 172, 1060, 196), copy=False)
        pt_ssr_icon = cv2.resize(pt_ssr_icon, None, fx=scaling, fy=scaling, interpolation=cv2.INTER_AREA)
        save_image(pt_ssr_icon, './assets/shop/event_cost/Pt.png')
        if self.event_shop_has_pt_ur:
            offset = 254
            pt_ur_icon = self.image_crop((1036 - offset, 172, 1060 - offset, 196), copy=False)
            pt_ur_icon = cv2.resize(pt_ur_icon, None, fx=scaling, fy=scaling, interpolation=cv2.INTER_AREA)
            save_image(pt_ur_icon, './assets/shop/event_cost/URPt.png')
        
    def _get_event_shop_cost(self):
        """
        Returns:
            np.array: [[x1, y1], [x2, y2]], location of the pt icon upper-left corner.
        """
        image = self.image_crop((472, 348, 1170, 625), copy=False)
        similarity = 0.5

        TEMPLATE_PT_SSR_ICON = Template('./assets/shop/event_cost/Pt.png')
        result = TEMPLATE_PT_SSR_ICON.match_multi(image, similarity=similarity, threshold=15)
        if self.event_shop_has_pt_ur:
            TEMPLATE_PT_UR_ICON = Template('./assets/shop/event_cost/URPt.png')
            result += TEMPLATE_PT_UR_ICON.match_multi(image, similarity=similarity, threshold=15)
        offsets = [(res.area[0] % 156, res.area[1] % 213) for res in result]
        offset = max(set(offsets), key=offsets.count, default=(0, 0))
        result = [res for res in result 
            if abs(res.area[0] % 156 - offset[0]) < 5 and abs(res.area[1] % 213 - offset[1]) < 5]
        logger.attr('Costs', f'{result}')
        return Points([(0., p.area[1]) for p in result]).group(threshold=5)

    @cached_property
    def event_shop_items(self):
        event_shop_items = EventShopItemGrid(
            grids=None, templates={}, template_area=(10, 10, 89, 70), 
            amount_area=(60, 71, 96, 97), price_area=(52, 132, 130, 165),
            tag_area=(0, 74, 1, 92), counter_area=(70, 167, 134, 186), 
        )
        event_shop_items.load_template_folder('./assets/shop/event')
        event_shop_items.load_cost_template_folder('./assets/shop/event_cost')
        return event_shop_items

    def _get_event_shop_grid(self):
        """
        Returns shop grid.

        Returns:
            ButtonGrid:
        """
        costs = self._get_event_shop_cost()
        row = len(costs)
        y = 0
        delta_y = 0

        if row == 1:
            y = costs[0][1] + 348 - (379 - 246)
            delta_y = 213
        elif row == 2:
            y = min(costs[0][1], costs[1][1]) + 348 - (379 - 246)
            delta_y = abs(costs[0][1] - costs[1][1])

        shop_grid = ButtonGrid(
            origin=(476, y), delta=(156, delta_y), button_shape=(98, 98), grid_shape=(5, row), name='EVENT_SHOP_GRID'
        )
        return shop_grid

    def event_shop_get_items(self, scroll_pos=None):
        """
        Args:
            scroll_pos (Float): Additional scroll position.

        Returns:
            list[Item]:
        """
        self.event_shop_items.grids = self._get_event_shop_grid()
        if self.config.SHOP_EXTRACT_TEMPLATE:
            self.event_shop_items.extract_template(self.device.image, './assets/shop/event')
        self.event_shop_items.predict(self.device.image, counter=True, scroll_pos=scroll_pos)
        shop_items = self.event_shop_items.items

        if len(shop_items):
            min_row = self.event_shop_items.grids[0, 0].area[1]
            row = [str(item) for item in shop_items if item.button[1] == min_row]
            logger.info(f'Shop row 1: {row}')
            row = [str(item) for item in shop_items if item.button[1] != min_row]
            logger.info(f'Shop row 2: {row}')
            return shop_items
        else:
            logger.info('No shop items found')
            return []

    def scan_all(self):
        """
        Returns:
            list[EventShopItem]:
        """
        items = []
        self.device.click_record.clear()

        logger.hr('Event Shop Scan', level=2)
        pre_pos, cur_pos = self.init_slider()

        while 1:
            pre_pos = self.pre_scroll(pre_pos, cur_pos)
            _items = self.event_shop_get_items(cur_pos)

            for _ in range(2):
                if not len(_items) or any(not item.is_known_item() for item in _items):
                    logger.warning('Empty Event shop or empty items, confirming')
                    self.device.sleep((0.3, 0.5))
                    self.device.screenshot()
                    _items = self.event_shop_get_items(cur_pos)
                    continue
                else:
                    items += _items
                    logger.info(f'Found {len(_items)} items at pos {cur_pos:.2f}')
                    break

            if EVENT_SHOP_SCROLL.at_bottom(main=self):
                logger.info('Event shop reach bottom, stop')
                break
            else:
                EVENT_SHOP_SCROLL.next_page(main=self, page=0.66)
                cur_pos = EVENT_SHOP_SCROLL.cal_position(main=self)
                continue
        self.device.click_record.clear()

        return items

    def event_shop_obstruct_handle(self):
        """
        Remove obstructions in shop view if any

        Returns:
            bool:
        """
        # Handle shop obstructions
        if self.appear(GET_SHIP, interval=1):
            logger.info(f'Shop obstruct: {GET_SHIP} -> {SHOP_CLICK_SAFE_AREA}')
            self.device.click(SHOP_CLICK_SAFE_AREA)
            return True
        # To lock new ships
        if self.handle_popup_confirm('SHOP_OBSTRUCT'):
            return True
        if self.appear(GET_ITEMS_1, interval=1):
            logger.info(f'Shop obstruct: {GET_ITEMS_1} -> {SHOP_CLICK_SAFE_AREA}')
            self.device.click(SHOP_CLICK_SAFE_AREA)
            return True
        if self.appear(GET_ITEMS_3, interval=1):
            logger.info(f'Shop obstruct: {GET_ITEMS_3} -> {SHOP_CLICK_SAFE_AREA}')
            self.device.click(SHOP_CLICK_SAFE_AREA)
            return True

        return False
    
    def event_shop_calculate_max_amount(self, item):
        count = item.count
        logger.attr("Item_count", count)

        MAX_AMOUNT = {
            "Coin": 600000,
            "Oil": 25000
        }
        if item.name in MAX_AMOUNT.keys():
            current = OCR_EVENT_SHOP_ITEM_REMAIN.ocr(self.device.image)
            limit = int((MAX_AMOUNT[item.name] - current) // item.price)
            if count > limit:
                logger.info(f"Item hard limit: {MAX_AMOUNT[item.name]}, Current stock: {current}")
                logger.info(f"Can buy: {limit}")
                count = limit
        
        if item.cost == "Pt":
            count = min(count, int((self._pt - self.pt_preserve)// item.price))
            logger.info(f"should buy: {count}")
        else:
            count = min(count, int(self._pt_ur // item.price))
            logger.info(f"should buy: {count}")
        
        return count
    
    def event_shop_handle_amount(self, item, amount=None, skip_first_screenshot=True):
        count = self.event_shop_calculate_max_amount(item)
        if count <= 1:
            return count
        
        self.interval_clear(AMOUNT_MAX)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(AMOUNT_MAX, offset=(50, 50), interval=3):
                continue

            if OCR_SHOP_AMOUNT.ocr(self.device.image) > 1:
                break
        
        if amount is not None:
            self.ui_ensure_index(amount, letter=OCR_SHOP_AMOUNT, prev_button=AMOUNT_MINUS, next_button=AMOUNT_PLUS,
                             skip_first_screenshot=True)
            logger.info(f"Set buy count to {amount}")
            return amount
        else:
            self.ui_ensure_index(count, letter=OCR_SHOP_AMOUNT, prev_button=AMOUNT_MINUS, next_button=AMOUNT_PLUS,
                             skip_first_screenshot=True)
            logger.info(f"Set buy count to {count}")
            return count

    def event_shop_buy_item(self, item, amount=None, skip_first_screenshot=True):
        bought_all = False
        amount_handled = False
        finished = False
        self.interval_clear(SHOP_BUY_CONFIRM)
        self.interval_clear(SHOP_BUY_CONFIRM_AMOUNT)

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.event_shop_obstruct_handle():
                self.interval_reset(BACK_ARROW)
                continue

            if not finished and self.appear(BACK_ARROW, offset=(20, 20), interval=5):
                self.device.click(item)
                continue

            if self.appear(AMOUNT_MAX, offset=(20, 20)):
                if amount_handled:
                    finished = True
                    self.device.click(SHOP_BUY_CONFIRM_AMOUNT)
                    continue
                else:
                    count = self.event_shop_handle_amount(item, amount)
                    amount_handled = True
                    if count == 0:
                        logger.warning(f'Cannot buy this item: {item.name}, please check your item storage is not full.')
                        self.device.click(SHOP_CLICK_SAFE_AREA)
                        finished = True
                        continue
                    if count == item.count:
                        bought_all = True
                    continue
            if self.appear_then_click(SHOP_BUY_CONFIRM, offset=(50, 50), interval=3):
                bought_all = True
                finished = True
                continue

            if self.handle_popup_confirm('SHOP_BUY'):
                continue

            # End
            if finished and self.appear(BACK_ARROW, offset=(20, 20), interval=5):
                break

        return bought_all

    def event_shop_get_items_to_buy(self, name, price, tag):
        """
        Args:
            name (str): Item name.
            price (int): Item price.

        Returns:
            EventShopItem:
        """
        items = self.event_shop_get_items()
        for _ in range(2):
            if not len(items) or any(not item.is_known_item() for item in items):
                logger.warning('Empty Event shop or empty items, confirming')
                self.device.sleep((0.3, 0.5))
                self.device.screenshot()
                items = self.event_shop_get_items()
                continue
            else:
                _items = [item for item in items if item.name == name and item.price == price and item.tag == tag]
                if len(_items):
                    return _items.pop()
        return None

    def event_shop_buy(self, item, amount=None, skip_first_screenshot=True):
        """
        Args:
            item: Item to buy

        Returns:
            bool: if bought all of the item
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.event_shop_obstruct_handle():
                self.interval_reset(BACK_ARROW)
                continue
            if self.appear(BACK_ARROW, interval=5):
                break
        
        self.device.click_record.clear()
        EVENT_SHOP_SCROLL.set(item.scroll_pos, main=self, skip_first_screenshot=skip_first_screenshot)
        _item = self.event_shop_get_items_to_buy(name=item.name, price=item.price, tag=item.tag)
        if _item is None:
            logger.warning(f'Item {item.name} not found at pos {item.scroll_pos:.2f}, skip.')
            return True
        elif self.event_shop_buy_item(_item, amount=amount, skip_first_screenshot=False):
            logger.info(f'Bought item: {_item.name}.')
            return True
        else:
            logger.info(f'Cannot buy all of item: {_item.name}.')
            return False
