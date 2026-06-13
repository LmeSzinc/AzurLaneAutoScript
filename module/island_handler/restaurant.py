from datetime import datetime, timedelta

import cv2
import numpy as np
from yaml import safe_load

from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property
from module.base.timer import Timer
from module.base.utils import color_similar, color_similarity_2d, load_image
from module.config.utils import get_server_next_update
from module.island.assets import ISLAND_CLICK_SAFE_AREA
from module.island.data import DIC_ISLAND_ITEM, DIC_ISLAND_RESTAURANT_MENU_TO_RECIPE
from module.island.utils import (
    load_hard_floor_items,
    load_item_mapping,
    load_request_buffer_items,
    load_reserve_items,
    normalize_item_keys,
)
from module.island_handler.assets import *
from module.island_handler.dock import IslandDock
from module.island_handler.dock_scanner import CharacterScanner
from module.logger import logger
from module.ocr.ocr import Digit
from module.statistics.item import Item, ItemGrid
from module.statistics.utils import load_folder


RESTAURANT_SWIPE_AREA = (583, 208, 1023, 400)
ISLAND_RESTAURANT_ITEM_ORDER_PRICE = {
    DIC_ISLAND_ITEM[item_id]['name']['en'].replace(' ', '_'): {
        'id': item_id,
        'order_price': DIC_ISLAND_ITEM[item_id]['order_price'],
    }
    for menu in DIC_ISLAND_RESTAURANT_MENU_TO_RECIPE.values()
    for item_id in menu.keys()
}


class WaitressOccupied(Exception):
    pass


class RestaurantItem(Item):
    IMAGE_SHAPE = (83, 87)

    def predict_valid(self):
        mask = color_similarity_2d(self.image, (207, 209, 211))
        cv2.inRange(mask, 0, 221, dst=mask)
        sum_ = np.count_nonzero(mask)
        return sum_ > 400


class RestaurantItemGrid(ItemGrid):
    item_class = RestaurantItem
    similarity = 0.75

    def __init__(self, grid: ButtonGrid):
        super().__init__(
            grid,
            templates={},
            template_area=(12, 21, 72, 67),
            amount_area=(38, 67, 83, 86),
            tag_area=(66, 2, 72, 5)
        )
        self.amount_ocr = Digit([], lang='cnocr', threshold=160, name='Amount_ocr')
        self.load_template_folder('./assets/island/restaurant')

    @staticmethod
    def predict_tag(image):
        color = cv2.mean(np.array(image))[:3]
        if color_similar(color, (79, 201, 108), threshold=30):
            return 'bonus'
        return None

    def predict(self, image, name=True, amount=True, cost=False, price=True, tag=True):
        super().predict(image, name=True, amount=True, cost=False, price=False, tag=True)
        for item in self.items:
            item.id = ISLAND_RESTAURANT_ITEM_ORDER_PRICE.get(item.name, {}).get('id', 0)
            item.price = ISLAND_RESTAURANT_ITEM_ORDER_PRICE.get(item.name, {}).get('order_price', 0)
        items = self.items
        grids = self.grids
        if len(items):
            min_row = grids[0, 0].area[1]
            row = [str(item) for item in items if item.button[1] == min_row]
            logger.info(f'Item row 1: {row}')
            row = [str(item) for item in items if item.button[1] != min_row]
            logger.info(f'Item row 2: {row}')
            return items


class IslandRestaurant(IslandDock):
    working_restaurant_id = None

    @staticmethod
    def get_initial_capacity_from_grade(grade):
        if grade == 'bronze':
            return 5
        elif grade in ['silver', 'gold', 'diamond']:
            return 6
        else:
            raise ValueError(f"Invalid grade: {grade}")

    def has_waitress(self, config_key, waitress_name):
        value = self.config.cross_get(config_key)
        if not isinstance(value, str):
            return False
        return waitress_name in value.split('+')

    @cached_property
    def restaurant_capacity(self):
        capacity = {
            601: self.get_initial_capacity_from_grade(self.config.cross_get("IslandBusiness.IslandRestaurant.KoiGrade")),
            602: self.get_initial_capacity_from_grade(self.config.cross_get("IslandBusiness.IslandRestaurant.BearGrade")),
            603: self.get_initial_capacity_from_grade(self.config.cross_get("IslandBusiness.IslandRestaurant.EateryGrade")),
            604: self.get_initial_capacity_from_grade(self.config.cross_get("IslandBusiness.IslandRestaurant.GrillGrade")),
            901: self.get_initial_capacity_from_grade(self.config.cross_get("IslandBusiness.IslandRestaurant.CafeGrade")),
        }
        if self.has_waitress("IslandBusiness.IslandRestaurant.KoiWaitress", 'Chao_Ho'):
            capacity[601] += 1
        if self.has_waitress("IslandBusiness.IslandRestaurant.BearWaitress", 'Cheshire'):
            capacity[602] += 1
        if self.has_waitress("IslandBusiness.IslandRestaurant.EateryWaitress", 'Helena'):
            capacity[603] += 1
        if self.has_waitress("IslandBusiness.IslandRestaurant.GrillWaitress", 'August_von_Parseval'):
            capacity[604] += 1
        if self.has_waitress("IslandBusiness.IslandRestaurant.CafeWaitress", 'Cheshire'):
            capacity[901] += 1
        return capacity

    @staticmethod
    def get_quantity_from_grade(grade):
        if grade in ['bronze', 'silver']:
            return 2
        elif grade == 'gold':
            return 3
        elif grade == 'diamond':
            return 4
        else:
            raise ValueError(f"Invalid grade: {grade}")

    @cached_property
    def restaurant_quantity(self):
        quantity = {
            601: self.get_quantity_from_grade(self.config.cross_get("IslandBusiness.IslandRestaurant.KoiGrade")),
            602: self.get_quantity_from_grade(self.config.cross_get("IslandBusiness.IslandRestaurant.BearGrade")),
            603: self.get_quantity_from_grade(self.config.cross_get("IslandBusiness.IslandRestaurant.EateryGrade")),
            604: self.get_quantity_from_grade(self.config.cross_get("IslandBusiness.IslandRestaurant.GrillGrade")),
            901: self.get_quantity_from_grade(self.config.cross_get("IslandBusiness.IslandRestaurant.CafeGrade")),
        }
        return quantity

    def is_in_island_restaurant(self):
        return self.appear(ISLAND_RESTAURANT_CHECK, offset=(0, 20))

    @cached_property
    def restaurant_has_event(self):
        return self.appear(ISLAND_RESTAURANT_EVENT_CHECK, offset=(20, 20))

    # 364 and 214
    @cached_property
    def _restaurant_offset_x(self):
        if self.restaurant_has_event:
            return 150
        else:
            return 0

    @cached_property
    def _restaurant_offset(self):
        return (self._restaurant_offset_x - 20, -20, self._restaurant_offset_x + 20, 20)

    def receive_revenue(self):
        confirm_timer = Timer(1, count=3)
        for _ in self.loop():
            if self.appear_then_click(ISLAND_RESTAURANT_RECEIVE, offset=self._restaurant_offset, interval=2):
                confirm_timer.reset()
                continue
            if self.appear(ISLAND_RESTAURANT_RESULT, offset=(20, 20), interval=2):
                self.device.click(ISLAND_CLICK_SAFE_AREA)
                confirm_timer.reset()
                continue
            if self.handle_island_additional():
                confirm_timer.reset()
                continue
            # End
            if (self.appear(ISLAND_RESTAURANT_RECOMMEND, offset=self._restaurant_offset)
                    or self.restaurant_resting()):
                if confirm_timer.reached():
                    return True

    @cached_property
    def restaurant_grid(self):
        return ButtonGrid(
            origin=(583 + self._restaurant_offset_x, 208), delta=(89.5, 92),
            button_shape=(83, 87), grid_shape=(5, 2), name='restaurant_grid'
        )

    def swipe_top_to_bottom(self):
        if not self.appear(ISLAND_RESTAURANT_SCROLL_TOP, offset=self._restaurant_offset):
            return False
        box = (RESTAURANT_SWIPE_AREA[0] + self._restaurant_offset_x, RESTAURANT_SWIPE_AREA[1],
               RESTAURANT_SWIPE_AREA[2] + self._restaurant_offset_x, RESTAURANT_SWIPE_AREA[3])
        self.device.swipe_vector((0, -150), box=box, padding=-5)
        for _ in self.loop(timeout=0.8):
            pass
        return True

    def swipe_bottom_to_top(self):
        if not self.appear(ISLAND_RESTAURANT_SCROLL_BOTTOM, offset=self._restaurant_offset):
            return False
        box = (RESTAURANT_SWIPE_AREA[0] + self._restaurant_offset_x, RESTAURANT_SWIPE_AREA[1],
               RESTAURANT_SWIPE_AREA[2] + self._restaurant_offset_x, RESTAURANT_SWIPE_AREA[3])
        self.device.swipe_vector((0, 150), box=box, padding=-5)
        for _ in self.loop(timeout=0.8):
            pass
        return True

    def scan_item_grid(self, grid: ButtonGrid):
        item_grid = RestaurantItemGrid(grid)
        if self.config.SHOP_EXTRACT_TEMPLATE:
            item_grid.extract_template(self.device.image, folder='./assets/island/restaurant')
        item_grid.predict(self.device.image, tag=True)
        return item_grid.items

    def scan_all_items(self):
        items = []
        items_set = set()
        self.swipe_bottom_to_top()
        result = self.scan_item_grid(self.restaurant_grid)
        for item in result:
            if item.name not in items_set:
                items.append(item)
                items_set.add(item.name)
        if self.swipe_top_to_bottom():
            result = self.scan_item_grid(self.restaurant_grid.move((0, 24)))
            for item in result:
                if item.name not in items_set:
                    items.append(item)
                    items_set.add(item.name)
        return items

    @cached_property
    def event_buff(self):
        if not self.restaurant_has_event:
            return 0
        ocr = Digit(ISLAND_RESTAURANT_EVENT_BUFF, lang='cnocr', letter=(67, 71, 23), threshold=160, alphabet='0123IDB')
        result = ocr.ocr(self.device.image)
        if not result in [10, 20, 30]:
            logger.warning(f'Unexpected event buff OCR result: {result}, default to 10')
            result = 10
        return result

    def get_sell_plan(self):
        capacity = self.restaurant_capacity[self.working_restaurant_id]
        menu_text = {
            601: self.config.cross_get("IslandBusiness.IslandRestaurant.KoiMenu", default="{}"),
            602: self.config.cross_get("IslandBusiness.IslandRestaurant.BearMenu", default="{}"),
            603: self.config.cross_get("IslandBusiness.IslandRestaurant.EateryMenu", default="{}"),
            604: self.config.cross_get("IslandBusiness.IslandRestaurant.GrillMenu", default="{}"),
            901: self.config.cross_get("IslandBusiness.IslandRestaurant.CafeMenu", default="{}"),
        }[self.working_restaurant_id]
        menu = normalize_item_keys(safe_load(menu_text))
        protected_items = self.restaurant_protected_items
        def total_revenue_estimate(item):
            amount = min(item.amount, capacity)
            if item.tag == 'bonus':
                return item.price * amount * (1 + self.event_buff / 100)
            return item.price * amount
        def sell_amount(item):
            return min(item.amount, capacity)
        def is_sellable_surplus(item):
            return item.amount - sell_amount(item) >= protected_items.get(item.id, 0)
        items = self.scan_all_items()
        menu_items = [
            item for item in items
            if item.id in menu
            and item.amount >= capacity
        ]
        surplus_items = [
            item for item in items
            if item.id not in menu
            and is_sellable_surplus(item)
        ]
        sellable_items = menu_items + surplus_items
        quantity = self.restaurant_quantity[self.working_restaurant_id]
        items = sorted(sellable_items, key=total_revenue_estimate, reverse=True)
        if len(items) < quantity:
            quantity = len(items)
        plan = items[:quantity]
        logger.info(f'Sell plan: {[str(item) for item in plan]}')
        return plan

    @cached_property
    def restaurant_protected_items(self):
        hard_floor_items = normalize_item_keys(load_hard_floor_items(
            self.config.cross_get("IslandProduction.IslandProduction.HardFloorItems", "")
        ))
        reserve_items = normalize_item_keys(load_reserve_items(
            self.config.cross_get("IslandProduction.IslandProduction.ReserveItems", "")
        ))
        request_buffer_items = normalize_item_keys(load_request_buffer_items(
            self.config.cross_get("IslandProduction.IslandProduction.RequestBufferItems", "")
        ))
        daily_buffer_items = normalize_item_keys(load_item_mapping(
            self.config.cross_get("IslandProduction.IslandProduction.DailyBufferItems", ""),
            config_name='DailyBufferItems',
        ))
        item_ids = set()
        item_ids.update(hard_floor_items)
        item_ids.update(reserve_items)
        item_ids.update(request_buffer_items)
        item_ids.update(daily_buffer_items)
        return {
            item_id: (
                hard_floor_items.get(item_id, 0)
                + reserve_items.get(item_id, 0)
                + max(request_buffer_items.get(item_id, 0), daily_buffer_items.get(item_id, 0))
            )
            for item_id in item_ids
        }

    @cached_property
    def waitress_lists(self):
        waitress_lists = {
            601: self.config.cross_get("IslandBusiness.IslandRestaurant.KoiWaitress").split("+") if isinstance(self.config.cross_get("IslandBusiness.IslandRestaurant.KoiWaitress"), str) else [],
            602: self.config.cross_get("IslandBusiness.IslandRestaurant.BearWaitress").split("+") if isinstance(self.config.cross_get("IslandBusiness.IslandRestaurant.BearWaitress"), str) else [],
            603: self.config.cross_get("IslandBusiness.IslandRestaurant.EateryWaitress").split("+") if isinstance(self.config.cross_get("IslandBusiness.IslandRestaurant.EateryWaitress"), str) else [],
            604: self.config.cross_get("IslandBusiness.IslandRestaurant.GrillWaitress").split("+") if isinstance(self.config.cross_get("IslandBusiness.IslandRestaurant.GrillWaitress"), str) else [],
            901: self.config.cross_get("IslandBusiness.IslandRestaurant.CafeWaitress").split("+") if isinstance(self.config.cross_get("IslandBusiness.IslandRestaurant.CafeWaitress"), str) else [],
        }
        return waitress_lists

    @cached_property
    def unavailable_waitress_list(self):
        lst = set()
        for restaurant_id, waitress_list in self.waitress_lists.items():
            if restaurant_id == self.working_restaurant_id:
                continue
            for waitress in waitress_list:
                if waitress == 'none':
                    break
                elif waitress == 'any':
                    continue
                else:
                    lst.add(waitress)
        lst = list(lst)
        return lst

    def restaurant_running(self):
        return self.appear(ISLAND_RESTAURANT_RUNNING, offset=self._restaurant_offset)

    def restaurant_resting(self):
        return self.appear(ISLAND_RESTAURANT_RESTING, offset=self._restaurant_offset)

    def choose_waitress(self):
        waitress_list = self.waitress_lists[self.working_restaurant_id]
        if waitress_list == ['none']:
            return False
        unavailable_waitress_list = self.unavailable_waitress_list
        for waitress in waitress_list:
            if waitress in unavailable_waitress_list:
                unavailable_waitress_list.remove(waitress)
        if unavailable_waitress_list:
            logger.warning(f"Unavailable waitress list: {unavailable_waitress_list}")
        for _ in self.loop():
            if self.appear_then_click(ISLAND_RESTAURANT_SELECT_CHARACTER, offset=self._restaurant_offset, interval=2):
                continue
            if self.is_in_island_dock():
                break
        success = True
        for waitress in waitress_list:
            if waitress != 'any':
                candidate = self.island_dock_find_character(waitress)
                if candidate is None:
                    self.ensure_dock_page_at_top()
                    success = self.island_dock_select_character_with_blacklist(self.unavailable_waitress_list) and success
                elif candidate.status == 'free':
                    self.island_dock_select_one(candidate.button)
                else:
                    time_until_update = get_server_next_update("00:00") - datetime.now()
                    if time_until_update < timedelta(hours=8):
                        self.ensure_dock_page_at_top()
                        success = self.island_dock_select_character_with_blacklist(self.unavailable_waitress_list) and success
                    else:
                        logger.warning(f"Waitress {waitress} not available, delaying restaurant {self.working_restaurant_id} for 8 hours")
                        self.ui_back(check_button=self.is_in_island_restaurant)
                        raise WaitressOccupied(f"Waitress {waitress} is occupied, delaying restaurant {self.working_restaurant_id} for 8 hours")
            else:
                success = self.island_dock_select_character_with_blacklist(self.unavailable_waitress_list) and success
        if not success:
            logger.warning("Failed to choose waitress")
            self.ui_back(check_button=self.is_in_island_restaurant)
        else:
            self.island_dock_select_confirm(check_button=self.is_in_island_restaurant, skip_first=False)
        return success

    def select_dishes(self):
        plan = self.get_sell_plan()
        self.swipe_bottom_to_top()
        result = self.scan_item_grid(self.restaurant_grid)
        plan_to_click = []
        for item in result:
            if item in plan:
                plan_to_click.append(item)
        for _ in self.loop():
            for item in plan_to_click:
                if self.is_button_selected(item._button):
                    plan.remove(item)
                    plan_to_click.remove(item)
                else:
                    self.device.click(item._button)
            if not plan_to_click:
                break
        if not plan:
            return True
        if self.swipe_top_to_bottom():
            result = self.scan_item_grid(self.restaurant_grid.move((0, 24)))
            plan_to_click = []
            for item in result:
                if item in plan:
                    plan_to_click.append(item)
            for _ in self.loop():
                for item in plan_to_click:
                    if self.is_button_selected(item._button):
                        plan.remove(item)
                        plan_to_click.remove(item)
                    else:
                        self.device.click(item._button)
                if not plan_to_click:
                    break
        return not plan

    def restaurant_start(self):
        for _ in self.loop():
            if self.handle_island_additional():
                continue
            if self.appear_then_click(ISLAND_RESTAURANT_START, offset=self._restaurant_offset, interval=2):
                continue
            if self.restaurant_running():
                return True

    def run(self):
        if self.restaurant_running():
            logger.info("Restaurant is already running, skip this round")
            return False
        self.receive_revenue()
        if self.restaurant_resting():
            logger.info("Restaurant is resting, finish this round")
            return False
        if not self.choose_waitress():
            logger.warning("Failed to choose waitress, skip this round")
            return False
        if not self.select_dishes():
            logger.warning("Failed to select all dishes, skip this round")
            return False
        if not self.restaurant_start():
            logger.warning("Failed to start restaurant, skip this round")
            return False
        return True
