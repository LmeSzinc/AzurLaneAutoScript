from datetime import datetime, timedelta

import cv2
from jellyfish import levenshtein_distance
import numpy as np

import module.config.server as server
from module.base.button import Button, ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import color_similarity_2d
from module.island.assets import *
from module.island.data import DIC_ISLAND_ITEM, DIC_ISLAND_SEASON_ORDER
from module.island.ui import IslandUI
from module.island.utils import load_hard_floor_items, load_reserve_items, normalize_item_keys
from module.island_handler.recipe import IslandReversedDigitCounter
from module.logger import logger
from module.map_detection.utils import Points
from module.ocr.ocr import Duration, Ocr
from module.ui.page import page_island_order


COLOR_REGULAR = (57, 189, 255)  # Blue
COLOR_REGULAR_COOLDOWN = (173, 227, 255)  # Light Blue
COLOR_SEASON = (255, 173, 27)  # Yellow
COLOR_URGENT = (135, 122, 239)  # Purple
# COLOR_EASY = (114, 225, 167)  # Green
# COLOR_HARD = (237, 128, 102)  # Red
EMPTY_SEASON_ORDER_ID = 0


def get_circles(image, color, inner_radius, outer_radius):
    """
    First use color_similarity_2d to create a mask of the image, then
    Use cv2.HoughCircles to detect circles in the image,
    and return the circles that are detected.
    """
    mask = color_similarity_2d(image, color=color)
    cv2.threshold(mask, 240, 255, cv2.THRESH_BINARY, dst=mask)
    blurred = cv2.GaussianBlur(mask, (7, 7), sigmaX=1.5, sigmaY=1.5)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=2*inner_radius,
                               param1=100, param2=30, minRadius=inner_radius-2, maxRadius=outer_radius+2)
    if circles is not None:
        circles = circles[0]
    else:
        circles = []
    return circles


def get_season_order_id(requirements):
    required_items = {
        item_id: counter[1] if isinstance(counter, (list, tuple)) and len(counter) > 1 else counter
        for item_id, counter in requirements.items()
    }
    for id, order in DIC_ISLAND_SEASON_ORDER.items():
        if required_items == order.get('request', {}):
            return id
    logger.warning(f'Cannot find season order id for requirements: {requirements}')
    return None


class IslandOrder(IslandUI):
    def detect_orders(self, color=COLOR_REGULAR):
        """
        Returns:
            (List[Button]): A list of Button objects that represent the detected orders in the page."""
        inner_radius = 44
        outer_radius = 52
        circles = get_circles(self.device.image, color, inner_radius, outer_radius)
        button_list = []
        for index, circle in enumerate(circles):
            x, y, _ = circle
            x = int(x)
            y = int(y)
            detect_area = (x - outer_radius, y - outer_radius, x + outer_radius, y + outer_radius)
            click_area = (x - inner_radius, y - inner_radius, x + inner_radius, y + inner_radius)
            button = Button(area=detect_area, color=(), button=click_area, name=f'ORDER_AT_{x}_{y}')
            button_list.append(button)
        return button_list

    @property
    def requirement_grid(self):
        return ButtonGrid(
            origin=(884, 240),
            delta=(0, 79),
            button_shape=(334, 78),
            grid_shape=(1, 3),
            name="REQUIREMENT_GRID"
        )

    @property
    def requirement_name_grid(self):
        name_grid = self.requirement_grid.crop((168, 12, 328, 40))
        return name_grid

    @property
    def requirement_counter_grid(self):
        counter_grid = self.requirement_grid.crop((238, 44, 327, 65))
        return counter_grid

    @cached_property
    def requirement_name_ocr(self):
        if server.server == 'jp':
            lang = 'jp'
        elif server.server == 'cn':
            lang = 'cnocr'
        else:
            lang = 'azur_lane'
        return Ocr(self.requirement_name_grid.buttons, lang=lang, letter=(57, 59, 61), threshold=160, name='REQUIREMENTS_NAME_OCR')

    @cached_property
    def requirement_counter_ocr(self):
        return IslandReversedDigitCounter(self.requirement_counter_grid.buttons, lang='cnocr', letter=(57, 59, 61), sub_letter=(253, 97, 96), name='REQUIREMENTS_COUNTER_OCR')

    def item_name_to_item_id(self, name):
        if name == '':
            return None
        if server.server == 'jp':
            # While we have 果樹園二重奏 and 朝光活力コンビ, the problem of カニ as 力二 is worse,
            # so we replace 力 with カ before matching,
            # which can fix most of the misrecognition without causing new issues.
            name = name.replace('二', 'ニ').replace('力', 'カ')
        min_distance = float('inf')
        corrected_name = None
        corrected_id = None
        item_lists = DIC_ISLAND_ITEM.keys()

        for item in item_lists:
            item_name = DIC_ISLAND_ITEM[item]['name'][server.server]
            distance = levenshtein_distance(name, item_name)
            if distance < min_distance:
                min_distance = distance
                corrected_name = item_name
                corrected_id = item

        if name != corrected_name:
            logger.info(f'Recipe product name OCR result "{name}" corrected to "{corrected_name}" with distance {min_distance}')
        return corrected_id

    def scan_current_order_requirements(self):
        name_ocr = self.requirement_name_ocr
        counter_ocr = self.requirement_counter_ocr
        names = name_ocr.ocr(self.device.image)
        ids = [self.item_name_to_item_id(name) for name in names]
        counters = counter_ocr.ocr(self.device.image)
        requirements = {}
        for id, counter in zip(ids, counters):
            if id is not None and counter is not None:
                requirements[id] = counter
        return requirements

    def get_order_remain_time(self, order_button: Button):
        time_button = order_button.crop((10, 119, 100, 145))
        print(f'OCR area: {time_button.area}')
        time_ocr = Duration(time_button, name='ORDER_REMAIN_TIME_OCR')
        remain_time = time_ocr.ocr(self.device.image)
        logger.info(f'Order remain time: {remain_time}')
        return remain_time

    @cached_property
    def hard_floor(self):
        hard_floor_items_text = load_hard_floor_items(
            self.config.cross_get("IslandProduction.IslandProduction.HardFloorItems", "")
        )
        return normalize_item_keys(hard_floor_items_text)

    @cached_property
    def reserve(self):
        reserve_items_text = load_reserve_items(
            self.config.cross_get("IslandProduction.IslandProduction.ReserveItems", "")
        )
        return normalize_item_keys(reserve_items_text)

    def is_order_satisfied(self, order_requirements, is_urgent=False):
        for item, counter in order_requirements.items():
            stock, required, _ = counter
            if not is_urgent:
                hard_floor = self.hard_floor.get(item, 0)
                reserve = self.reserve.get(item, 0)
                effective_stock = stock - hard_floor - reserve
            else:
                hard_floor = 0
                reserve = 0
                effective_stock = stock
            if required > effective_stock:
                logger.warning(
                    f'Item {item} does not meet the requirement: stock {stock}, '
                    f'hard floor {hard_floor}, reserve {reserve}, '
                    f'effective stock {effective_stock}, required {required}'
                )
                return False
        return True

    def handle_island_order_level_up(self):
        if self.appear(ISLAND_ORDER_LEVEL_UP, offset=(20, 20), interval=1):
            logger.info('Detected island order level up')
            self.device.click(ISLAND_CLICK_SAFE_AREA)
            return True
        return False

    def click_order(self, order_button):
        click_timer = Timer(1, count=3)
        for _ in self.loop(timeout=5, skip_first=False):
            if click_timer.reached():
                self.device.click(order_button)
                click_timer.reset()
                continue
            if self.appear(ISLAND_ORDER_REQUIREMENTS_CHECK, offset=(0, 20)):
                logger.info('Clicked order button, requirements page appeared')
                break
            if self.appear(ISLAND_ORDER_COOLDOWN_SPEED_UP, offset=(20, 20)):
                logger.info('Clicked order button, cooldown speed up page appeared')
                break
        else:
            logger.info('click timer timeout, assuming requirements page appeared')

    def submit_order(self, is_urgent=False):
        if is_urgent:
            submit_button = ISLAND_ORDER_ACCEPT_URGENT
        else:
            submit_button = ISLAND_ORDER_ACCEPT
        confirm_timer = Timer(3, count=6).start()
        clicked = False
        for _ in self.loop(timeout=20):
            if self.handle_island_additional():
                clicked = True
                confirm_timer.reset()
                continue
            if self.handle_island_order_level_up():
                confirm_timer.reset()
                continue
            if not clicked and self.match_template_color(submit_button, offset=(20, 20), interval=1):
                self.device.click(submit_button)
                confirm_timer.reset()
                continue
            if not confirm_timer.reached():
                continue
            if self.match_template_color(ISLAND_ORDER_BACKGROUND, offset=(20, 20)):
                logger.info('Submit success')
                return True
            if is_urgent and self.match_template_color(ISLAND_ORDER_ACCEPT, offset=(20, 20)):
                logger.info('Urgent order submit success')
                return True
            if not is_urgent and self.match_template_color(ISLAND_ORDER_COOLDOWN_SPEED_UP, offset=(20, 20)):
                logger.info('Previous order submitted, wait for next order to appear')
                continue
            if clicked and self.match_template_color(ISLAND_ORDER_ACCEPT, offset=(20, 20)):
                logger.info('Confirm timer timeout, assuming submit success')
                return True
        else:
            logger.warning('Submit order timeout, something may be wrong')
            return False

    @property
    def cooldown_time_ocr(self):
        time_ocr = Duration(ISLAND_ORDER_COOLDOWN_REMAIN_TIME, letter=(57, 59, 61), name='ORDER_COOLDOWN_REMAIN_TIME_OCR')
        return time_ocr

    def reject_order(self):
        for _ in self.loop():
            if self.appear_then_click(ISLAND_ORDER_REJECT, offset=(20, 20), interval=1):
                continue
            if self.appear(ISLAND_ORDER_COOLDOWN_SPEED_UP, offset=(20, 20)):
                break
        cooldown_remain_time = self.cooldown_time_ocr.ocr(self.device.image)
        logger.info(f'Order cooldown remain time: {cooldown_remain_time}')
        return cooldown_remain_time

    next_runtime = []
    update_production_plan = False

    def update_stuck_season_order(self, order_id):
        order_id = order_id or EMPTY_SEASON_ORDER_ID
        previous_id = self.config.cross_get("IslandOrder.IslandOrder.StuckSeasonOrderId", EMPTY_SEASON_ORDER_ID)
        if order_id != previous_id:
            logger.info(f'Updating stuck season order id from {previous_id} to {order_id}')
            self.config.cross_set("IslandOrder.IslandOrder.StuckSeasonOrderId", order_id)
            self.update_production_plan = True

    def execute_order(self, order_button, is_urgent=False, is_season=False):
        """
        Returns:
            (bool): True if the order is dealt.
        """
        self.click_order(order_button)
        if self.appear(ISLAND_ORDER_COOLDOWN_SPEED_UP, offset=(20, 20)):
            logger.warning('Order is in cooldown, cannot submit')
            remain_time = self.cooldown_time_ocr.ocr(self.device.image)
            next_runtime = datetime.now() + remain_time
            self.next_runtime.append(next_runtime)
            return False
        requirements = self.scan_current_order_requirements()
        if self.is_order_satisfied(requirements, is_urgent=is_urgent):
            return self.submit_order(is_urgent=is_urgent)
        else:
            logger.warning('Order requirements not satisfied due to low stock')
            if is_urgent:
                logger.warning('Urgent order can only be delayed')
                remain_time = self.get_order_remain_time(order_button)
                if remain_time == timedelta(0):
                    logger.warning('Urgent order remain time ocr error, default to 8 hours')
                    remain_time = timedelta(hours=8)
                else:
                    logger.warning(f'Order remain time: {remain_time}')
                next_runtime = datetime.now() + remain_time
                self.next_runtime.append(next_runtime)
                return False
            elif is_season:
                logger.warning('Season order can only be abandoned, skip this order')
                stuck_season_order_id = get_season_order_id(requirements)
                self.update_stuck_season_order(stuck_season_order_id)
                return False
            else:
                remain_time = self.reject_order()
                next_runtime = datetime.now() + remain_time
                self.next_runtime.append(next_runtime)
                return True

    regular_orders = []
    regular_cooldown_orders = []
    urgent_orders = []
    season_orders = []

    def detect_all_orders(self):
        self.regular_cooldown_orders = self.detect_orders(color=COLOR_REGULAR_COOLDOWN)
        self.regular_orders = self.detect_orders(color=COLOR_REGULAR)
        for order in self.regular_orders:
            for cooldown_order in self.regular_cooldown_orders:
                if np.linalg.norm(np.array(order.button) - np.array(cooldown_order.button)) < 10:
                    self.regular_orders.remove(order)
                    break
        self.urgent_orders = self.detect_orders(color=COLOR_URGENT)
        if len(self.urgent_orders) > 1:
            logger.warning(f'Multiple urgent orders detected, which is unexpected: {len(self.urgent_orders)}')
            self.urgent_orders = self.urgent_orders[:1]
        self.season_orders = self.detect_orders(color=COLOR_SEASON)
        if len(self.season_orders) > 1:
            logger.warning(f'Multiple season orders detected, which is unexpected: {len(self.season_orders)}')
            self.season_orders = self.season_orders[:1]

    def run_any_order(self):
        for order in self.urgent_orders:
            if self.execute_order(order, is_urgent=True, is_season=False):
                logger.info('Urgent order submitted')
            else:
                logger.info('Urgent order delayed')
        for order in self.regular_orders:
            if self.execute_order(order, is_urgent=False, is_season=False):
                logger.info('Regular order submitted')
                return True
            else:
                logger.info('Regular order rejected')
        for order in self.season_orders:
            if self.execute_order(order, is_urgent=False, is_season=True):
                logger.info('Season order submitted')
                return True
            else:
                logger.info('Season order abandoned')
        return False

    def run(self):
        self.ui_ensure(page_island_order)
        self.next_runtime = []
        self.update_production_plan = False
        for _ in self.loop():
            self.detect_all_orders()
            if self.run_any_order():
                continue
            else:
                logger.info('No order can be submitted')
                break
        if not self.season_orders:
            self.update_stuck_season_order(EMPTY_SEASON_ORDER_ID)
        if self.update_production_plan:
            logger.info('Production plan needs to be updated due to stuck season order change')
            from module.island_handler.production_planner import IslandProductionPlanner
            IslandProductionPlanner(self.config, self.device).run()
            self.update_production_plan = False
        for order in self.regular_cooldown_orders:
            remain_time = self.get_order_remain_time(order)
            if remain_time == timedelta(0):
                logger.warning('Order remain time ocr error, click to check')
                self.click_order(order)
                remain_time = self.cooldown_time_ocr.ocr(self.device.image)
            next_runtime = datetime.now() + remain_time
            self.next_runtime.append(next_runtime)
        if self.next_runtime:
            next_runtime = min(self.next_runtime)
            logger.info(f'Next order runtime: {next_runtime}')
            self.config.task_delay(target=next_runtime, server_update=True)
        else:
            self.config.task_delay(server_update=True)
