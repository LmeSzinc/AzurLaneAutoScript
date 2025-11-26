import cv2

from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import color_similarity_2d, crop
from module.combat.assets import GET_SHIP, GET_ITEMS_1, GET_ITEMS_3
from module.logger import logger
from module.map_detection.utils import Points
from module.shop.assets import AMOUNT_PLUS, AMOUNT_MINUS, AMOUNT_MAX, SHOP_BUY_CONFIRM_AMOUNT, SHOP_BUY_CONFIRM, \
    SHOP_CLICK_SAFE_AREA
from module.shop.clerk import OCR_SHOP_AMOUNT
from module.shop_event.assets import *
from module.shop_event.item import ITEM_SHAPE, EventShopItemGrid, DELTA_PRICE_BACKGROUND, DELTA_ITEM, \
    PRICE_BACKGROUND_COLOR, PRICE_THRESHOLD
from module.shop_event.ui import EventShopUI, EVENT_SHOP_SCROLL
from module.ui_white.assets import BACK_ARROW_WHITE

DETECT_AREA = (221, 194, 1049, 632)


class ItemNotFoundError(Exception):
    pass


class EventShopClerk(EventShopUI):
    pt_image = None
    urpt_image = None

    def _get_event_shop_grid(self):
        mask = color_similarity_2d(self.device.image, PRICE_BACKGROUND_COLOR)
        cv2.inRange(mask, PRICE_THRESHOLD, 255, dst=mask)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=8)
        mask = crop(mask,
                    (DETECT_AREA[0], DETECT_AREA[1] + DELTA_PRICE_BACKGROUND[1], DETECT_AREA[2], DETECT_AREA[3]),
                    copy=False)
        buttons = TEMPLATE_COST_PRICE_BACKGROUND.match_multi(mask, similarity=0.6)
        points = Points([(0., p.area[1]) for p in buttons]).group(threshold=5)

        row = len(points)
        if row == 2:
            y = min(points[0][1], points[1][1]) + DETECT_AREA[1]
            delta_y = abs(points[0][1] - points[1][1])
        elif row == 1:
            y = points[0][1] + DETECT_AREA[1]
            delta_y = 215
        else:
            logger.warning(f"Unexpected number of rows: {row}, assuming scroll at top.")
            y = 1 + DETECT_AREA[1]  # Start position is 1 pixel lower than detect area
            delta_y = 215

        shop_grid = ButtonGrid(
            origin=(DETECT_AREA[0] + DELTA_ITEM[0], y + DELTA_ITEM[1]),
            delta=(169, delta_y),
            button_shape=ITEM_SHAPE,
            grid_shape=(5, row),
            name="EVENT_SHOP_GRID",
        )
        return shop_grid

    @cached_property
    def event_shop_items(self):
        event_shop_items = EventShopItemGrid(grids=None, templates={})
        event_shop_items.load_template_folder('./assets/shop/event')
        return event_shop_items

    def event_shop_get_items(self, scroll_pos=None):
        self.event_shop_items.grids = self._get_event_shop_grid()
        if self.config.SHOP_EXTRACT_TEMPLATE:
            self.event_shop_items.extract_template(self.device.image, './assets/shop/event')
        self.event_shop_items.predict(self.device.image, name=True, amount=True, cost=False,
                                      price=True, tag=True, counter=True, scroll_pos=scroll_pos)
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
        items = []
        self.device.click_record_clear()

        logger.hr('Event Shop Scan', level=2)
        EVENT_SHOP_SCROLL.set_top(main=self)
        while 1:
            new_items = self.event_shop_get_items(scroll_pos=EVENT_SHOP_SCROLL.cal_position(main=self))
            if len(items):
                old_last_row = [item for item in items if item.button[1] == items[-1].button[1]]
                new_first_row = [item for item in new_items if item.button[1] == new_items[0].button[1]]
                new_second_row = [item for item in new_items if item.button[1] != new_items[0].button[1]]
                if len(old_last_row) == len(new_first_row) and all(
                        old.name == new.name for old, new in zip(old_last_row, new_first_row)):
                    logger.info('Ignore duplicated items')
                    items += new_second_row
                else:
                    items += new_items
            else:
                items += new_items
            if EVENT_SHOP_SCROLL.at_bottom(main=self):
                logger.info('Event shop reach bottom')
                break
            else:
                EVENT_SHOP_SCROLL.next_page(main=self, page=0.66)
                continue
        return items

    def event_shop_buy_item(self, item_to_buy, amount=None):
        scroll_pos = item_to_buy.scroll_pos
        EVENT_SHOP_SCROLL.set(scroll_pos, main=self)
        items = self.event_shop_get_items()
        items = [item for item in items if item.name == item_to_buy.name
                 and item.count == item_to_buy.count and item.price == item_to_buy.price]
        if len(items) == 0:
            logger.error(f'Item {item_to_buy} not found at scroll position {scroll_pos}')
            logger.warning(f'Will try to rerun the task.')
            raise ItemNotFoundError(f'Item {item_to_buy} not found at scroll position {scroll_pos}')
        elif len(items) > 1:
            logger.warning(f'Multiple items found for {item_to_buy} at scroll position {scroll_pos}, '
                           f'buying the first one')
        item = items[0]
        # For ship items, while it may have multiple stock, can only buy one at a time.
        if getattr(item, 'is_ship', False):
            buy_times = item.count if amount is None else min(amount, item.count)
            for _ in range(buy_times):
                self.event_shop_buy_item_execute(item, amount=1)
        else:
            self.event_shop_buy_item_execute(item, amount=amount)

    def event_shop_buy_item_execute(self, item, amount):
        self.event_shop_handle_obstruct()
        executed = False
        amount_handled = False
        timer = Timer(2, count=4).start()
        for _ in self.loop():
            if self.appear(AMOUNT_MAX, offset=(20, 20)):
                if not amount_handled:
                    self.device.click(AMOUNT_MAX)
                    if amount is not None:
                        self.ui_ensure_index(amount, letter=OCR_SHOP_AMOUNT, prev_button=AMOUNT_MINUS,
                                             next_button=AMOUNT_PLUS,
                                             skip_first_screenshot=False)
                    amount_handled = True
                    timer.reset()
                    continue
                else:
                    self.device.click(SHOP_BUY_CONFIRM_AMOUNT)
                    executed = True
                    timer.reset()
                    continue
            elif self.appear(SHOP_BUY_CONFIRM, offset=(20, 20)):
                self.device.click(SHOP_BUY_CONFIRM)
                executed = True
                timer.reset()
                continue
            elif self.appear(BACK_ARROW_WHITE, offset=(20, 20)):
                if not executed:
                    self.device.click(item)
                    timer.reset()
                    continue
                elif timer.reached():
                    break
            elif timer.reached() and self.event_shop_handle_obstruct():
                timer.reset()
                continue

    def event_shop_handle_obstruct(self):
        if self.handle_info_bar():
            return True
        if self.handle_get_meowfficer():
            return True
        if self.appear(GET_SHIP, offset=(20, 20), interval=2):
            logger.info(f'Shop obstruct: {GET_SHIP} -> {SHOP_CLICK_SAFE_AREA}')
            self.device.click(SHOP_CLICK_SAFE_AREA)
            return True
        if self.appear(GET_ITEMS_1, offset=(20, 20), interval=2):
            logger.info(f'Shop obstruct: {GET_ITEMS_1} -> {SHOP_CLICK_SAFE_AREA}')
            self.device.click(SHOP_CLICK_SAFE_AREA)
            return True
        if self.appear(GET_ITEMS_3, offset=(20, 20), interval=2):
            logger.info(f'Shop obstruct: {GET_ITEMS_3} -> {SHOP_CLICK_SAFE_AREA}')
            self.device.click(SHOP_CLICK_SAFE_AREA)
            return True
        return False
