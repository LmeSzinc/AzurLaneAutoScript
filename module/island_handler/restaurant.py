import cv2
import numpy as np
from yaml import safe_load

import module.config.server as server
from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import color_mask, color_similar
from module.island.assets import ISLAND_CLICK_SAFE_AREA
from module.island.data import (
    DIC_ISLAND_ITEM,
    DIC_ISLAND_RECIPE,
    DIC_ISLAND_RESTAURANT_MENU_TO_RECIPE,
)
from module.island.utils import (
    get_task_target_items,
    item_name_with_id,
    load_hard_floor_items,
    load_item_mapping,
    normalize_item_keys,
    production_place_name_with_id,
)
from module.island_handler.assets import *
from module.island_handler.dock import IslandDock, dock_grade_key, dock_identity_set
from module.island_handler.restaurant_config import (
    RESTAURANT_IDS,
    WAITRESS_ANY,
    WAITRESS_NONE,
    get_config_key,
    get_menu_reserve_items,
    get_restaurant_capacity,
    get_restaurant_config,
    get_selected_named_waitresses,
    get_waitress_slots,
)
from module.logger import logger
from module.ocr.ocr import Digit
from module.statistics.item import Item, ItemGrid

RESTAURANT_SWIPE_AREA = (583, 208, 1023, 400)
_RESTAURANT_ITEM_IDS = {
    item_id
    for menu in DIC_ISLAND_RESTAURANT_MENU_TO_RECIPE.values()
    for item_id in menu.keys()
}
# Seasonal restaurant recipes are kept in the general recipe table instead of
# the current menu rotation.  Their item data marks them as restaurant food
# with manage_influence=250, so derive these entries from the same business
# data rather than maintaining a second list of historical IDs.
_RESTAURANT_ITEM_IDS.update(
    item_id
    for recipe in DIC_ISLAND_RECIPE.values()
    for item_id in recipe.get('commission_product', {})
    if DIC_ISLAND_ITEM.get(item_id, {}).get('manage_influence') == 250
)
ISLAND_RESTAURANT_ITEM_ORDER_PRICE = {
    DIC_ISLAND_ITEM[item_id]['name']['en'].replace(' ', '_'): {
        'id': item_id,
        'order_price': DIC_ISLAND_ITEM[item_id]['order_price'],
    }
    for item_id in _RESTAURANT_ITEM_IDS
}


def restaurant_item_log_text(item, sell_amount=None):
    name = item_name_with_id(item.id) if item.id and item.id in DIC_ISLAND_ITEM else item.name
    detail = f'stock {item.amount}'
    if sell_amount is not None:
        detail += f', sell {sell_amount}'
    if getattr(item, 'tag', None) == 'bonus':
        detail += ', event bonus'
    return f'{name} ({detail})'


def waitress_requests_match(requests, identities, blacklist=()):
    """Check whether zero, one, or two distinct identities fit the requests."""
    requests = [request for request in requests if request != WAITRESS_NONE]
    identities = list(identities)
    blacklist = set(blacklist)
    if len(requests) > 2 or len(identities) > len(requests):
        return False
    if len(identities) != len(set(identities)):
        return False
    if any(identity in blacklist or identity in (None, '', 'unknown') for identity in identities):
        return False
    if not identities:
        return True

    def match(request, identity):
        allowed = dock_identity_set(request)
        return identity != 'Workerjuu' if allowed is None else identity in allowed

    if len(identities) == 1:
        return any(match(request, identities[0]) for request in requests)
    if len(requests) != 2:
        return False
    return (
        match(requests[0], identities[0]) and match(requests[1], identities[1])
    ) or (
        match(requests[0], identities[1]) and match(requests[1], identities[0])
    )


class RestaurantItem(Item):
    IMAGE_SHAPE = (83, 87)

    def predict_valid(self):
        # Mask pixels that are not similar to the background
        mask = color_mask(self.image, (207, 209, 211), threshold=50)
        cv2.bitwise_not(mask, dst=mask)
        sum_ = cv2.countNonZero(mask)
        return sum_ > 400


class RestaurantItemAmount(Digit):
    def pre_process(self, image):
        image = super().pre_process(image)
        image = cv2.copyMakeBorder(image, 4, 2, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        return image


class RestaurantItemGrid(ItemGrid):
    item_class = RestaurantItem
    similarity = 0.75

    def __init__(self, grid: ButtonGrid):
        super().__init__(
            grid,
            templates={},
            template_area=(12, 21, 72, 67),
            amount_area=(42, 67, 77, 85),
            tag_area=(66, 2, 72, 5)
        )
        if server.server == 'jp':
            self.amount_ocr = RestaurantItemAmount([], letter=(220, 220, 220), lang='azur_lane', threshold=128, name='Amount_ocr')
        else:
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
            row = [restaurant_item_log_text(item) for item in items if item.button[1] == min_row]
            logger.info(f'Item row 1: {row}')
            row = [restaurant_item_log_text(item) for item in items if item.button[1] != min_row]
            logger.info(f'Item row 2: {row}')
            return items


class IslandRestaurant(IslandDock):
    working_restaurant_id = None

    @cached_property
    def restaurant_capacity(self):
        return {
            restaurant_id: get_restaurant_capacity(self.config, restaurant_id)
            for restaurant_id in RESTAURANT_IDS
        }

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
        quantity = {}
        for restaurant_id in RESTAURANT_IDS:
            config_data = get_restaurant_config(restaurant_id)
            grade = self.config.cross_get(
                get_config_key(restaurant_id, config_data['grade_key'])
            )
            quantity[restaurant_id] = self.get_quantity_from_grade(grade)
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
            offset = 150
        else:
            offset = 0
        logger.attr('restaurant_offset_x', offset)
        return offset

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
        if not self.match_template_color(ISLAND_RESTAURANT_SCROLL_TOP, offset=self._restaurant_offset):
            return False
        box = (RESTAURANT_SWIPE_AREA[0] + self._restaurant_offset_x, RESTAURANT_SWIPE_AREA[1],
               RESTAURANT_SWIPE_AREA[2] + self._restaurant_offset_x, RESTAURANT_SWIPE_AREA[3])
        self.device.swipe_vector((0, -150), box=box, padding=-5)
        for _ in self.loop(timeout=0.8):
            pass
        return True

    def swipe_bottom_to_top(self):
        if not self.match_template_color(ISLAND_RESTAURANT_SCROLL_BOTTOM, offset=self._restaurant_offset):
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
        menu_key = get_restaurant_config(self.working_restaurant_id)['menu_key']
        menu_text = self.config.cross_get(
            get_config_key(self.working_restaurant_id, menu_key),
            default="{}",
        )
        menu = normalize_item_keys(safe_load(menu_text))
        protected_items = self.restaurant_protected_items
        def total_revenue_estimate(item):
            amount = min(item.amount, capacity)
            if item.tag == 'bonus':
                return item.price * amount * (1 + self.event_buff / 100)
            return item.price * amount
        def has_sellable_capacity(item):
            return item.amount >= capacity + protected_items.get(item.id, 0)
        items = self.scan_all_items()
        menu_items = [
            item for item in items
            if item.id in menu
            # Sell one full waitress-capacity tranche while preserving manual
            # hard floors, task targets, and remaining season-order
            # requirements. Configured menu sales may consume their soft
            # restaurant reserve and daily buffer.
            and has_sellable_capacity(item)
        ]
        quantity = self.restaurant_quantity[self.working_restaurant_id]
        plan = sorted(menu_items, key=total_revenue_estimate, reverse=True)[:quantity]
        remaining = quantity - len(plan)
        if remaining:
            # Fill only vacant shelves from stock above the complete operating floor.
            daily_buffer_items = normalize_item_keys(load_item_mapping(
                self.config.cross_get("IslandProduction.IslandProduction.DailyBufferItems", "{}"),
                config_name='DailyBufferItems',
            ))
            manual_buffer_items = normalize_item_keys(load_item_mapping(
                self.config.cross_get("IslandProduction.IslandProduction.ManualBufferItems", "{}"),
                config_name='ManualBufferItems',
            ))
            menu_reserve_items = get_menu_reserve_items(self.config)
            def has_surplus_capacity(item):
                operation_floor = (
                    protected_items.get(item.id, 0)
                    + menu_reserve_items.get(item.id, 0)
                    + max(daily_buffer_items.get(item.id, 0), manual_buffer_items.get(item.id, 0), 0)
                )
                return item.amount >= capacity + operation_floor
            surplus_items = [
                item for item in items
                if item.id not in menu and has_surplus_capacity(item)
            ]
            plan.extend(sorted(surplus_items, key=total_revenue_estimate, reverse=True)[:remaining])
        restaurant = production_place_name_with_id(self.working_restaurant_id)
        menu_summary = ', '.join(
            f'{item_name_with_id(item_id)} x{amount}'
            for item_id, amount in sorted(menu.items())
        ) or '-'
        plan_summary = ', '.join(
            restaurant_item_log_text(item, sell_amount=capacity) for item in plan
        ) or '-'
        logger.info(f'Restaurant configured menu for {restaurant}: {menu_summary}')
        logger.info(f'Restaurant sell plan for {restaurant}: {plan_summary}')
        return plan

    @cached_property
    def restaurant_protected_items(self):
        hard_floor_items = normalize_item_keys(load_hard_floor_items(
            self.config.cross_get("IslandProduction.IslandProduction.HardFloorItems", "")
        ))
        protected_target_items = get_task_target_items(self.config)
        item_ids = set(hard_floor_items) | set(protected_target_items)
        return {
            item_id: max(hard_floor_items.get(item_id, 0), 0)
            + max(protected_target_items.get(item_id, {}).get('total_need_count', 0), 0)
            for item_id in item_ids
        }

    @cached_property
    def waitress_lists(self):
        return {
            restaurant_id: list(get_waitress_slots(self.config, restaurant_id))
            for restaurant_id in RESTAURANT_IDS
        }

    def unavailable_waitress_list(self):
        current_waitresses = get_selected_named_waitresses(
            get_waitress_slots(self.config, self.working_restaurant_id)
        )
        lst = set()
        for restaurant_id in RESTAURANT_IDS:
            if restaurant_id == self.working_restaurant_id:
                continue
            lst.update(
                get_selected_named_waitresses(
                    get_waitress_slots(self.config, restaurant_id)
                )
            )
        return sorted(lst - current_waitresses)

    def restaurant_running(self):
        return self.appear(ISLAND_RESTAURANT_RUNNING, offset=self._restaurant_offset)

    def restaurant_resting(self):
        return self.appear(ISLAND_RESTAURANT_RESTING, offset=self._restaurant_offset)

    def choose_waitress(self):
        self.waitress_occupied = False
        active_waitresses = [
            waitress for waitress in get_waitress_slots(self.config, self.working_restaurant_id)
            if waitress != WAITRESS_NONE
        ]
        if not active_waitresses or len(active_waitresses) > 2:
            return False

        blacklist = set(self.unavailable_waitress_list())
        required = {waitress for waitress in active_waitresses if waitress != WAITRESS_ANY}
        if blacklist:
            logger.warning(f"Unavailable waitress list: {sorted(blacklist)}")
        if required & blacklist:
            logger.warning(f"Required waitresses are blacklisted: {sorted(required & blacklist)}")
            return False

        for _ in self.loop(timeout=10):
            if self.is_in_island_dock():
                break
            if self.appear_then_click(ISLAND_RESTAURANT_SELECT_CHARACTER, offset=self._restaurant_offset, interval=2):
                continue
        else:
            logger.warning('Failed to enter restaurant character selection')
            return False

        selected = set()

        def handle_page(characters):
            while True:
                occupied = {
                    character.identity for character in characters
                    if character.status == 'occupied'
                }
                if required & occupied:
                    self.waitress_occupied = True
                    logger.warning(f"Required waitresses are occupied: {sorted(required & occupied)}")
                    return False

                for character in characters:
                    if self.is_button_selected(character.button, color=(19, 181, 231)):
                        if character.status != 'free':
                            return False
                        selected.add(character.identity)

                if not waitress_requests_match(active_waitresses, selected, blacklist):
                    logger.warning("Selected waitresses do not satisfy restaurant requests")
                    return False
                if len(selected) == len(active_waitresses):
                    return True

                for character in sorted(characters, key=dock_grade_key):
                    if character.identity in selected or character.status != 'free':
                        continue
                    # Check both assignments. An early `any` choice must not
                    # consume the only character suitable for a named role.
                    if not waitress_requests_match(
                            active_waitresses, selected | {character.identity}, blacklist):
                        continue
                    if not self.island_dock_select_one(character.button):
                        logger.warning("Failed to select waitress, cancel restaurant")
                        return False
                    selected.add(character.identity)
                    if len(selected) == len(active_waitresses):
                        return True
                    # Even on the same page, discard buttons after a click.
                    characters = self.island_dock_scan_page()
                    if not characters:
                        return False
                    break
                else:
                    return None

        success, _ = self.island_dock_search(handle_page, descending=True)
        if success is not True:
            logger.warning("Failed to choose waitress")
            self.island_dock_quit()
            return False
        self.island_dock_select_confirm(check_button=self.is_in_island_restaurant, skip_first=False)
        return True

    def select_dishes(self):
        plan = self.get_sell_plan()
        if not plan:
            return False
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
        if plan:
            restaurant = production_place_name_with_id(self.working_restaurant_id)
            remaining = [restaurant_item_log_text(item) for item in plan]
            logger.warning(f'Failed to select dishes for {restaurant}; remaining: {remaining}')
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
