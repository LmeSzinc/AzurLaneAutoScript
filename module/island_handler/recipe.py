from datetime import datetime
import re

import cv2
from jellyfish import levenshtein_distance
import numpy as np
from yaml import safe_load

import module.config.server as server
from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property
from module.base.timer import Timer
from module.base.utils import color_similarity_2d, extract_letters, random_rectangle_vector_opted
from module.exception import GameTooManyClickError
from module.island.data import DIC_ISLAND_ITEM, DIC_ISLAND_RECIPE, DIC_ISLAND_SHOP_ITEM_TO_RECIPE, DIC_ISLAND_SLOT
from module.island.utils import (
    ceil_div_or_ceil,
    get_target_stock_load_rate,
    load_hard_floor_items,
    load_item_mapping,
    load_request_buffer_items,
    load_reserve_items,
    normalize_item_keys,
    normalize_item_needs,
    parse_item_need_deadlines,
)
from module.island_handler.assets import *
from module.island_handler.shop import IslandShop
from module.logger import logger
from module.map_detection.utils import Points
from module.ocr.ocr import Digit, Duration, Ocr
from module.ui.page import page_island, page_island_manage, page_island_shop


class IslandProductionRestart(Exception):
    pass


RECIPE_SIZE = (280, 134)
RECIPE_DELTA = (0, 149)
RECIPE_DETECT_AREA = (181, 55, 460, 668)
RECIPE_DRAG_AREA = (300, 55, 350, 668)
RECIPE_ANCHOR_AREA = (58, 97, 102, 115)
RECIPE_PRODUCT_NAME_AREA = (123, 23, 269, 46)
RECIPE_PRODUCT_STOCK_AREA = (212, 92, 275, 110)
if server.server == 'jp':
    lang = 'jp'
elif server.server == 'en':
    lang = 'azur_lane'
else:
    lang = 'cnocr'
RECIPE_PRODUCT_NAME_OCR = Ocr([], lang=lang, letter=(57, 59, 61), threshold=160, name='product_name_ocr')
RECIPE_PRODUCT_STOCK_OCR = Digit([], lang='cnocr', letter=(80, 80, 80), threshold=160, name='product_stock_ocr')
ISLAND_RECIPE_AMOUNT_OCR = Digit(ISLAND_RECIPE_AMOUNT, letter=(50, 50, 57), name='recipe_amount_ocr')


class IslandReversedDigitCounter(Ocr):
    def __init__(self, buttons, lang='cnocr', letter=(255, 255, 255), sub_letter=None, threshold=128, sub_threshold=128, alphabet='0123456789/IDSB()+',
                 name=None):
        super().__init__(buttons, lang=lang, letter=letter, threshold=threshold, alphabet=alphabet, name=name)
        self.sub_letter = sub_letter
        self.sub_threshold = sub_threshold

    def pre_process(self, image, background_color=(80, 80, 80)):
        mask = color_similarity_2d(image, background_color)
        mask[mask < self.threshold] = 0
        line = cv2.bitwise_and(mask[0], mask[-1]).flatten()
        indices = np.where(line > 200)[0]
        left = indices[0] if len(indices) > 0 else 0
        right = indices[-1] + 1 if len(indices) > 0 else len(line)
        image = image[:, left:right]

        main_image = extract_letters(image, letter=self.letter, threshold=self.threshold)
        if self.sub_letter is not None and isinstance(self.sub_letter, tuple):
            mask = color_similarity_2d(image, self.sub_letter)
            mask[mask < self.sub_threshold] = 0
            if np.count_nonzero(mask) > 50:
                sub_image = extract_letters(image, letter=self.sub_letter, threshold=self.sub_threshold)
                cv2.bitwise_and(main_image, sub_image, dst=main_image)

        return main_image

    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('I', '1').replace('D', '0').replace('S', '5')
        result = result.replace('B', '8')
        if re.fullmatch(r'\d+/?', result):
            normalized = f'{result.rstrip("/")}/0'
            logger.warning(f'Unexpected ocr result: {result}, normalized to {normalized}')
            result = normalized
        result = re.search(r'(\d+)/([\d+\-\*\(\)]+)', result)
        if result:
            numerator = int(result.group(1))
            denominator_str = result.group(2)
            try:
                denominator = eval(denominator_str)
                current, total = denominator, numerator
                return total, current, total - current
            except (ValueError, SyntaxError):
                logger.warning(f'Unexpected ocr result: {result.group(0)}')
                return 0, 0, 0
        else:
            logger.warning(f'Unexpected ocr result: {result}')
            return 0, 0, 0


RECIPE_INGREDIENT_COUNTER_OCR = IslandReversedDigitCounter(
    [], lang='cnocr', letter=(255, 255, 255), sub_letter=(253, 171, 34),
    threshold=160, sub_threshold=160, name='ingredient_counter_ocr'
)


def get_recipe_product_id(recipe_id):
    return next(iter(DIC_ISLAND_RECIPE[recipe_id]['commission_product']))


def get_target_stock_weight(stock, target_stock):
    if stock >= target_stock or target_stock <= 0:
        return 0
    else:
        return (target_stock - stock) / target_stock


def get_target_stock_batch_weight(stock, target_stock, batch_size):
    if stock >= target_stock:
        return 0
    else:
        return (target_stock - stock) / batch_size


def get_demand_weight(stock, target_stock, batch_size, demand):
    demand_deadlines = demand
    if len(demand_deadlines) == 2 and isinstance(demand_deadlines[0], (int, float, np.integer, np.floating)):
        demand_deadlines = [demand_deadlines]
    rate_per_day = get_target_stock_load_rate(stock, target_stock, demand_deadlines)
    if rate_per_day <= 0:
        return 0
    else:
        return rate_per_day / batch_size


def get_idle_accumulating_weight(stock, target_stock, demand, idle_accumulating):
    if idle_accumulating <= 0:
        return float('inf')
    else:
        if len(demand) == 2 and isinstance(demand[0], (int, float, np.integer, np.floating)):
            demand_stock, _ = demand
        else:
            demand_stock = demand[-1][0] if demand else 0
        effective_stock = max(stock - target_stock - demand_stock, 0)
        return effective_stock / idle_accumulating


def get_recipe_entry_weight(entry):
    _, (stock, target_stock, _hard_floor, _reserve, batch_size, demand, idle_accumulating) = entry
    return (
        get_demand_weight(stock, target_stock, batch_size, demand),
        get_target_stock_weight(stock, target_stock),
        get_target_stock_batch_weight(stock, target_stock, batch_size),
        -get_idle_accumulating_weight(stock, target_stock, demand, idle_accumulating),
        -stock
    )


def recipe_product_name_to_recipe_id(name, slotcode=None):
    if server.server == 'jp':
        # While we have 果樹園二重奏 and 朝光活力コンビ, the problem of カニ as 力二 is worse,
        # so we replace 力 with カ before matching,
        # which can fix most of the misrecognition without causing new issues.
        name = name.replace('二', 'ニ').replace('力', 'カ')
    min_distance = float('inf')
    min_real_distance = float('inf')
    corrected_name = None
    corrected_id = None
    if isinstance(slotcode, int):
        recipe_lists = DIC_ISLAND_SLOT[slotcode]['formula'] + DIC_ISLAND_SLOT[slotcode]['activity_formula']
    else:
        recipe_lists = DIC_ISLAND_RECIPE.keys()

    for recipe_id in recipe_lists:
        product_id = get_recipe_product_id(recipe_id)
        product_name = DIC_ISLAND_ITEM[product_id]['name'][server.server]

        # If product_name is longer than OCR result name, try matching any substring
        # of product_name with the same length as name and take the minimal distance.
        if isinstance(name, str) and isinstance(product_name, str) and len(product_name) >= len(name) and len(name) > 0:
            best_sub_distance = float('inf')
            L = len(name)
            for i in range(len(product_name) - L + 1):
                sub = product_name[i:i+L]
                d = levenshtein_distance(name, sub)
                if d < best_sub_distance:
                    best_sub_distance = d
            distance = best_sub_distance
            real_distance = levenshtein_distance(name, product_name)
        else:
            distance = levenshtein_distance(name, product_name)
            real_distance = distance
        if distance < min_distance or (distance == min_distance and real_distance < min_real_distance):
            min_distance = distance
            min_real_distance = real_distance
            corrected_name = product_name
            corrected_id = recipe_id

    if name != corrected_name:
        logger.info(f'Recipe product name OCR result "{name}" corrected to "{corrected_name}" with distance {min_distance} and real distance {min_real_distance}')
    return corrected_id


class IslandRecipe(IslandShop):
    working_slot_id = None

    # recipe related methods
    def is_in_recipe_menu(self):
        return self.appear(ISLAND_RECIPE_CHECK, offset=(20, 20))

    def _get_recipe_buttons(self):
        area = (RECIPE_DETECT_AREA[0] + RECIPE_ANCHOR_AREA[0],
                RECIPE_DETECT_AREA[1] + RECIPE_ANCHOR_AREA[1],
                RECIPE_DETECT_AREA[2] - RECIPE_SIZE[0] + RECIPE_ANCHOR_AREA[2],
                RECIPE_DETECT_AREA[3] - RECIPE_SIZE[1] + RECIPE_ANCHOR_AREA[3])
        image = self.image_crop(area, copy=True)
        anchors = TEMPLATE_ISLAND_RECIPE_ANCHOR.match_multi(image, similarity=0.5, threshold=5)
        logger.attr('Recipe_in_view', len(anchors))
        rows = Points([(0., a.area[1]) for a in anchors]).group(threshold=5)
        return rows

    @cached_property
    def recipe_grid(self):
        for _ in self.loop(timeout=2):
            grid = self.get_recipe_grid()
            if len(grid.buttons) >= 3:
                return grid
        return grid

    def get_recipe_grid(self):
        rows = self._get_recipe_buttons()
        count = len(rows)
        delta_y = RECIPE_DELTA[1]
        if count > 4:
            logger.warning(f'Found {count} recipe anchors, which is more than expected, fixing count to 4')
            count = 4
        if count >= 2:
            y_list = rows[:, 1]
            y1, y2 = y_list[0], y_list[-1]
            origin_y = min(y1, y2) + RECIPE_DETECT_AREA[1]
        else:
            logger.warning('Unable to find enough recipe anchors, assume recipes are at top')
            origin_y = 114

        recipe_grid = ButtonGrid(
            origin=(181, origin_y), delta=(0, delta_y), button_shape=RECIPE_SIZE,
            grid_shape=(1, count), name='RECIPE_GRID'
        )
        return recipe_grid

    @cached_property
    def recipe_ids(self):
        return self.get_recipe_ids()

    def get_recipe_ids(self):
        product_name_grid = self.recipe_grid.crop(RECIPE_PRODUCT_NAME_AREA, name='RECIPE_PRODUCT_NAME_GRID')
        product_name_images = [self.image_crop(button.area, copy=True) for button in product_name_grid.buttons]
        product_names = RECIPE_PRODUCT_NAME_OCR.ocr(product_name_images, direct_ocr=True)
        corrected_ids = [recipe_product_name_to_recipe_id(name, slotcode=self.working_slot_id) for name in product_names]
        return corrected_ids

    def get_recipe_product_stocks(self):
        stock_grid = self.recipe_grid.crop(RECIPE_PRODUCT_STOCK_AREA, name='RECIPE_PRODUCT_STOCK_GRID')
        stock_images = [self.image_crop(button.area, copy=True) for button in stock_grid.buttons]
        stocks = RECIPE_PRODUCT_STOCK_OCR.ocr(stock_images, direct_ocr=True)
        return stocks

    def next_recipe_page(self):
        if len(self.recipe_grid.buttons) < 3:
            logger.info('Less than 3 recipes in current page, no need to swipe to next page')
            return
        else:
            p1, p2 = random_rectangle_vector_opted((0, -300), box=RECIPE_DRAG_AREA, padding=0)
            self.device.drag(p1, p2, hold_duration=0.1, name='RECIPE_NEXT_PAGE_SWIPE')
            del_cached_property(self, 'recipe_grid')
            del_cached_property(self, 'recipe_ids')
            self.device.screenshot()

    def prev_recipe_page(self):
        if len(self.recipe_grid.buttons) < 3:
            logger.info('Less than 3 recipes in current page, no need to swipe to previous page')
            return
        else:
            p1, p2 = random_rectangle_vector_opted((0, 300), box=RECIPE_DRAG_AREA, padding=0)
            self.device.drag(p1, p2, hold_duration=0.1, name='RECIPE_PREV_PAGE_SWIPE')
            del_cached_property(self, 'recipe_grid')
            del_cached_property(self, 'recipe_ids')
            self.device.screenshot()

    def scan_all_recipe_stocks(self):
        for _ in self.loop(timeout=3):
            # use ISLAND_RECIPE_AMOUNT_MAX as a check to ensure the recipe page is fully loaded
            if self.appear(ISLAND_RECIPE_AMOUNT_MAX, offset=(0, 20)):
                break
        all_stocks = {}
        drag_count = 0
        for _ in self.loop(timeout=30):
            new_stocks = dict(zip(self.recipe_ids, self.get_recipe_product_stocks()))
            all_stocks.update(new_stocks)
            self.next_recipe_page()
            drag_count += 1
            if ISLAND_RECIPE_DRAG_CHECK.match(self.device.image):
                if drag_count > 1:
                    logger.info(f'Ensured recipe page bottom after dragging {drag_count} times')
                    self.device.click_record_clear()
                    break
            else:
                drag_count = 0
                ISLAND_RECIPE_DRAG_CHECK.load_color(self.device.image)
        return all_stocks

    @cached_property
    def all_recipe_stocks(self):
        return self.scan_all_recipe_stocks()

    @cached_property
    def recipe_id_sequence(self):
        return self.get_recipe_id_sequence_to_run()

    @cached_property
    def hard_floor_items(self):
        yaml_text = self.config.cross_get("IslandProduction.IslandProduction.HardFloorItems", "")
        return normalize_item_keys(load_hard_floor_items(yaml_text))

    @cached_property
    def reserve_items(self):
        yaml_text = self.config.cross_get("IslandProduction.IslandProduction.ReserveItems", "")
        return normalize_item_keys(load_reserve_items(yaml_text))

    def get_recipe_id_sequence_to_run(
            self,
            daily_buffer_items_dict=None,
            request_buffer_items_dict=None,
            hard_floor_items_dict=None,
            reserve_items_dict=None,
            idle_accumulating_items_dict=None,
            task_target_items_dict=None,
    ):
        stocks_dict = self.all_recipe_stocks
        if daily_buffer_items_dict is None:
            yaml_text = self.config.cross_get("IslandProduction.IslandProduction.DailyBufferItems", "")
            if yaml_text is None:
                yaml_text = ""
            daily_buffer_items_dict = safe_load(yaml_text) or {}
        daily_buffer_items_dict = normalize_item_keys(daily_buffer_items_dict)
        if request_buffer_items_dict is None:
            yaml_text = self.config.cross_get("IslandProduction.IslandProduction.RequestBufferItems", "")
            request_buffer_items_dict = load_request_buffer_items(yaml_text)
        request_buffer_items_dict = normalize_item_keys(request_buffer_items_dict)
        if hard_floor_items_dict is None:
            hard_floor_items_dict = self.hard_floor_items
        else:
            hard_floor_items_dict = normalize_item_keys(hard_floor_items_dict)
        if reserve_items_dict is None:
            reserve_items_dict = self.reserve_items
        else:
            reserve_items_dict = normalize_item_keys(reserve_items_dict)
        if task_target_items_dict is None:
            yaml_text = self.config.cross_get("IslandSeasonTask.IslandSeasonTask.TaskTarget", "{}")
            task_target_items_dict = load_item_mapping(yaml_text, config_name='TaskTarget')
        task_target_items_dict = normalize_item_needs(task_target_items_dict, default_period=10)
        if idle_accumulating_items_dict is None:
            yaml_text = self.config.cross_get("IslandProduction.IslandProduction.IdleAccumulatingItems", "")
            if yaml_text is None:
                yaml_text = ""
            idle_accumulating_items_dict = safe_load(yaml_text) or {}
        idle_accumulating_items_dict = normalize_item_keys(idle_accumulating_items_dict)
        recipe_entry_sequence = []
        for recipe_id, stock in stocks_dict.items():
            recipe_product = DIC_ISLAND_RECIPE[recipe_id]['commission_product']
            product_id = get_recipe_product_id(recipe_id)
            batch_size = recipe_product[product_id]
            daily_consumed_stock = daily_buffer_items_dict.get(product_id, 0)
            request_buffer = request_buffer_items_dict.get(product_id, 0)
            hard_floor = hard_floor_items_dict.get(product_id, 0)
            reserve = reserve_items_dict.get(product_id, 0)
            target_stock = hard_floor + reserve + max(daily_consumed_stock, request_buffer)
            demand = task_target_items_dict.get(product_id, {})
            demand = parse_item_need_deadlines(demand)
            demand_text = ', '.join(
                f'{count} items in {period:g} days'
                for count, period in demand
            ) or '0 items in 1 days'
            idle_accumulating = idle_accumulating_items_dict.get(product_id, 0)
            recipe_entry_sequence.append((
                recipe_id,
                (stock, target_stock, hard_floor, reserve, batch_size, demand, idle_accumulating)
            ))
            logger.info(
                f'Recipe {recipe_id} stock: {stock}, '
                f'daily_consumed_stock: {daily_consumed_stock}, '
                f'request_buffer: {request_buffer}, '
                f'hard_floor: {hard_floor}, '
                f'reserve: {reserve}, '
                f'target_stock: {target_stock}, '
                f'batch_size: {batch_size}, task_target: {demand_text}, '
                f'idle accumulating rate: {idle_accumulating}'
            )
            logger.info(f'Recipe {recipe_id} weight: {get_recipe_entry_weight(recipe_entry_sequence[-1])}')
        recipe_entry_sequence.sort(key=lambda x: get_recipe_entry_weight(x), reverse=True)
        sorted_recipe_id_sequence = [x[0] for x in recipe_entry_sequence]
        logger.info(f'Calculated recipe id sequence to run: {sorted_recipe_id_sequence}')
        return recipe_entry_sequence

    @staticmethod
    def calculate_recipe_run_count(info):
        stock, target_stock, _hard_floor, _reserve, batch_size, demand, idle_accumulating = info
        rate_per_day = get_target_stock_load_rate(stock, target_stock, demand)
        if rate_per_day > 0:
            return ceil_div_or_ceil(rate_per_day, batch_size)
        if stock < target_stock:
            return (target_stock - stock - 1) // batch_size + 1
        if idle_accumulating <= 0:
            return 0
        return float('inf')

    def get_active_recipe_id(self):
        for recipe_id, button in zip(self.recipe_ids, self.recipe_grid.buttons):
            if self.is_button_selected(button):
                product_id = get_recipe_product_id(recipe_id)
                product_name = DIC_ISLAND_ITEM[product_id]['name'][server.server]
                logger.info(f'Selected recipe id: {recipe_id}, product name: {product_name}')
                return recipe_id
        logger.warning('Unable to determine selected recipe, assume no active recipe')
        return None

    def get_recipe_ingredient_grids(self, recipe_id=None):
        if recipe_id is None:
            recipe_id = self.get_active_recipe_id()
        if recipe_id is None:
            return None

        recipe_cost = DIC_ISLAND_RECIPE[recipe_id]['commission_cost']
        count = len(recipe_cost)
        logger.attr('Ingredient_count', count)
        if count == 0:
            return ButtonGrid(
                origin=(750, 474), delta=(0, 0), button_shape=(82, 83), grid_shape=(0, 1), name='RECIPE_INGREDIENT_GRID'
            )
        elif count == 1:
            return ButtonGrid(
                origin=(750, 474), delta=(0, 0), button_shape=(82, 83), grid_shape=(1, 1), name='RECIPE_INGREDIENT_GRID'
            )
        elif count == 2:
            return ButtonGrid(
                origin=(663, 474), delta=(175, 0), button_shape=(82, 83), grid_shape=(2, 1), name='RECIPE_INGREDIENT_GRID'
            )
        elif count == 3:
            return ButtonGrid(
                origin=(634, 474), delta=(116, 0), button_shape=(82, 83), grid_shape=(3, 1), name='RECIPE_INGREDIENT_GRID'
            )
        else:
            logger.warning(f'Unexpected ingredient count {count}, unable to determine ingredient grid')
            return None

    def get_recipe_ingredient_counters(self):
        active_recipe_id = self.get_active_recipe_id()
        ingredient_grids = self.get_recipe_ingredient_grids(active_recipe_id)
        if ingredient_grids is None:
            return None

        counter_grids = ingredient_grids.crop((-10, 66, 92, 83), name='counter_grids')
        for _ in self.loop(timeout=3):
            counter_images = [self.image_crop(button.area, copy=True) for button in counter_grids.buttons]
            counters = RECIPE_INGREDIENT_COUNTER_OCR.ocr(counter_images, direct_ocr=True)
            if (0, 0, 0) not in counters:
                break
        return counters

    def set_recipe(self, recipe_id):
        all_recipe_ids = list(self.all_recipe_stocks.keys())
        clicked = False
        for _ in self.loop(timeout=30):
            if clicked and self.get_active_recipe_id() == recipe_id:
                self.device.click_record_clear()
                return True
            if recipe_id in self.recipe_ids:
                index = self.recipe_ids.index(recipe_id)
                button = self.recipe_grid.buttons[index]
                self.device.click(button)
                clicked = True
                continue
            if all_recipe_ids.index(recipe_id) < all_recipe_ids.index(self.recipe_ids[0]):
                self.prev_recipe_page()
            else:
                self.next_recipe_page()
            clicked = False
        else:
            logger.warning(f'Unable to find recipe id {recipe_id} after looping through recipe pages, failed to set recipe')
            self.device.click_record_clear()
            return False

    def goto_ingredient_shop_page(self, entrance_button):
        click_timer = Timer(1, count=3).reset()
        for _ in self.loop(timeout=15):
            if self.appear(ISLAND_INFO_GOTO_SHOP, offset=(20, 20)):
                break
            if self.is_in_recipe_menu():
                if click_timer.reached_and_reset():
                    self.device.click(entrance_button)
        else:
            logger.warning('Unable to find ingredient button, failed to goto ingredient shop page')
            return False
        for _ in self.loop(timeout=15, skip_first=False):
            if self.appear_then_click(ISLAND_INFO_GOTO_SHOP, offset=(20, 20), interval=2):
                continue
            if self._island_shop_side_navbar.get_info(main=self)[0] == 0:
                return True
        else:
            logger.warning('Unable to find shop page in ingredient info page, failed to goto ingredient shop page')
            return False

    def prepare_ingredients(self, recipe_id, batch_count=float('inf')):
        # use this before setting recipe batch count to read out current ingredient need per batch,
        # since ranch recipes may have boosted ingredient requirement for higher batch production.
        counters = self.get_recipe_ingredient_counters()
        recipe_cost = DIC_ISLAND_RECIPE[recipe_id]['commission_cost']
        if batch_count == float('inf'):
            max_count = DIC_ISLAND_RECIPE[recipe_id]['production_limit']
            for ingredient_key, counter in zip(recipe_cost, counters):
                if ingredient_key in DIC_ISLAND_SHOP_ITEM_TO_RECIPE:
                    continue
                available_stock = max(counter[0] - self.hard_floor_items.get(ingredient_key, 0), 0)
                count = available_stock // counter[1] if counter[1] > 0 else float('inf')
                if count < max_count:
                    max_count = count
            batch_count = max_count
            logger.info(f'Calculated max batch count to produce with current ingredient stock: {batch_count}')
        success = True
        real_count = batch_count
        ingredient_buttons = self.get_recipe_ingredient_grids(recipe_id).buttons
        for ingredient_key, counter, button in zip(recipe_cost, counters, ingredient_buttons):
            hard_floor = self.hard_floor_items.get(ingredient_key, 0)
            available_stock = max(counter[0] - hard_floor, 0)
            if available_stock < real_count * counter[1]:
                if ingredient_key in DIC_ISLAND_SHOP_ITEM_TO_RECIPE:
                    if ingredient_key == 3004:  # flour cannot be bought via jumping page, need to go to shop page to buy
                        self.ui_back(check_button=page_island_manage.check_button)
                        self.ui_goto_island_shop()
                        isolated = False
                    else:
                        self.goto_ingredient_shop_page(entrance_button=button)
                        isolated = True
                    delta = real_count * counter[1] - available_stock
                    success = super().island_shop_buy({ingredient_key: delta}, isolated=isolated) and success
                    if not isolated:
                        # We need an exception for inherited class to handle ui switch
                        # and restart the ingredient preparation after buying flour,
                        # since flour purchase requires going into shop page and back,
                        # which may cause the recipe page to lose the set recipe and ingredient states.
                        self.ui_back(check_button=page_island.check_button)
                        self.ui_goto(page_island_manage)
                        raise IslandProductionRestart
                    else:
                        self.ui_back(check_button=self.is_in_recipe_menu)
                    if not success:
                        logger.warning(f'Failed to buy ingredient {ingredient_key} from shop, insufficient ingredient for recipe production')
                        real_count = min(real_count, available_stock // counter[1]) if counter[1] > 0 else 0
                else:
                    logger.warning(
                        f'Ingredient {ingredient_key} cannot be bought from shop, '
                        f'insufficient ingredient for recipe production after hard floor {hard_floor}'
                    )
                    real_count = min(real_count, available_stock // counter[1]) if counter[1] > 0 else 0
                    success = False
        return success, real_count

    def set_recipe_batch_count(self, batch_count=float('inf')):
        for _ in self.loop():
            if self.appear_then_click(ISLAND_RECIPE_AMOUNT_MAX, offset=(20, 20)):
                self.device.screenshot()
                break
        if batch_count == float('inf'):
            logger.info('Set recipe amount to max')
            return True
        else:
            logger.info(f'Set recipe amount to {batch_count}')
            if ISLAND_RECIPE_AMOUNT_OCR.ocr(self.device.image) < batch_count:
                # Check if already at max, if so, cannot set to desired amount
                counters = self.get_recipe_ingredient_counters()
                for counter in counters:
                    if counter[2] < 0:
                        logger.warning('Insufficient ingredient for next recipe amount, cannot set recipe amount to desired value')
                        return False
            try:
                self.ui_ensure_index(index=batch_count, letter=ISLAND_RECIPE_AMOUNT_OCR,
                                 next_button=ISLAND_RECIPE_AMOUNT_PLUS,
                                 prev_button=ISLAND_RECIPE_AMOUNT_MINUS,)
                return True
            except GameTooManyClickError:
                logger.warning('Too many clicks when setting recipe amount, failed to set recipe amount')
                return False

    def get_recipe_remain_time(self):
        if self.match_template_color(ISLAND_RECIPE_TIME_ANCHOR, offset=(100, 20)):
            ISLAND_RECIPE_TIME.load_offset(ISLAND_RECIPE_TIME_ANCHOR)
            remain_time = Duration(ISLAND_RECIPE_TIME.button, lang='cnocr', name='recipe_remain_time').ocr(self.device.image)
            return remain_time
        else:
            logger.warning('Unable to find recipe time anchor, failed to execute recipe')
            return None

    def run_recipe(self, recipe_id, batch_count=float('inf')):
        """
        Returns:
            tuple[timedelta, int | float]: remain time and actual batch count after starting,
                or None if failed to start recipe
        """
        self.last_unavailable_product = None
        if not self.is_in_recipe_menu():
            logger.warning('Not in recipe menu, cannot run recipe')
            return None
        if not self.set_recipe(recipe_id):
            logger.warning(f'Failed to set recipe to {recipe_id}, cannot run recipe')
            return None
        success, real_count = self.prepare_ingredients(recipe_id, batch_count=batch_count)
        if not success:
            logger.warning(f'Failed to prepare enough ingredient for {batch_count} batch(es) production')
            if real_count == 0:
                logger.warning('No batch can be produced with current ingredient stock, cannot run recipe')
                self.last_unavailable_product = get_recipe_product_id(recipe_id)
                return None
            else:
                logger.info(f'Can only produce {real_count} batch(es) with current ingredient stock, will try to run with this amount')
        if not self.set_recipe_batch_count(real_count):
            logger.warning(f'Failed to set recipe batch count to {"max" if real_count == float("inf") else real_count}, cannot run recipe')
            return None
        remain_time = self.get_recipe_remain_time()
        logger.attr('Recipe_remain_time', remain_time)
        if remain_time is not None:
            for _ in self.loop():
                if self.appear_then_click(ISLAND_RECIPE_TIME_ANCHOR, offset=(100, 20), interval=2):
                    continue
                if not self.is_in_recipe_menu():
                    break
            logger.info(f'Recipe {recipe_id} started with amount {"max" if real_count == float("inf") else real_count}, remain time: {remain_time}')
            return remain_time, real_count
        else:
            logger.warning('Failed to get recipe remain time, recipe may not have started successfully')
            return None

    def update_recipe_id_sequence_and_stock(self, recipe_id, batch_count):
        old_list = self.recipe_id_sequence
        new_list = []
        recipe_cost = DIC_ISLAND_RECIPE[recipe_id]['commission_cost']
        consumed_items = {
            item_id: amount * batch_count
            for item_id, amount in recipe_cost.items()
        }
        for old_recipe_id, info in old_list:
            product_id = get_recipe_product_id(old_recipe_id)
            if old_recipe_id == recipe_id:
                stock, target_stock, hard_floor, reserve, batch_size, demand, idle_accumulating = info
                new_stock = stock + batch_size * batch_count
                new_list.append((old_recipe_id, (
                    new_stock, target_stock, hard_floor, reserve, batch_size, demand, idle_accumulating
                )))
                logger.info(f'Updated recipe {recipe_id} stock from {stock} to {new_stock} after running recipe for {batch_count} batch(es)')
            elif product_id in consumed_items:
                stock, target_stock, hard_floor, reserve, batch_size, demand, idle_accumulating = info
                new_stock = stock - consumed_items[product_id]
                new_list.append((old_recipe_id, (
                    new_stock, target_stock, hard_floor, reserve, batch_size, demand, idle_accumulating
                )))
                logger.info(
                    f'Updated recipe {old_recipe_id} stock from {stock} to {new_stock} '
                    f'after consuming {consumed_items[product_id]} item(s) for recipe {recipe_id}'
                )
            else:
                new_list.append((old_recipe_id, info))
        # sort new_list by weight and update recipe_id_sequence
        new_recipe_entry_sequence = sorted(new_list, key=lambda x: get_recipe_entry_weight(x), reverse=True)
        self.recipe_id_sequence = new_recipe_entry_sequence
        self.all_recipe_stocks[recipe_id] += batch_size * batch_count
        for old_recipe_id, info in old_list:
            product_id = get_recipe_product_id(old_recipe_id)
            if product_id in consumed_items:
                self.all_recipe_stocks[old_recipe_id] -= consumed_items[product_id]

    def run(self, slot_id=None):
        """
        Returns:
            target_time (datetime): timestamp of when the recipe will finish, or None if failed to run any recipe
        """
        self.working_slot_id = slot_id
        del_cached_property(self, 'recipe_grid')
        del_cached_property(self, 'recipe_ids')
        while self.recipe_id_sequence:
            recipe_id, info = self.recipe_id_sequence[0]
            production_limit = DIC_ISLAND_RECIPE[recipe_id]['production_limit']
            batch_count = self.calculate_recipe_run_count(info)
            logger.info(f"Plan to run {batch_count} batch(es) of recipe {recipe_id}, limitation: {production_limit} batches")
            if batch_count <= 0:
                logger.info(f'Recipe {recipe_id} has no production demand, skip')
                self.recipe_id_sequence.pop(0)
                continue
            if batch_count > production_limit:
                logger.info(f"Will try to run {production_limit} batches")
                batch_count = production_limit
            result = self.run_recipe(recipe_id, batch_count)
            if result is not None:
                remain_time, real_count = result
                target_time = datetime.now() + remain_time
                logger.info(f'Will run recipe {recipe_id} for {real_count} batch(es), expected target time: {target_time}')
                self.update_recipe_id_sequence_and_stock(recipe_id, real_count)
                return target_time
            else:
                unavailable_product = getattr(self, 'last_unavailable_product', None)
                if unavailable_product is not None:
                    logger.info(
                        f'Product {unavailable_product} is unavailable after recipe {recipe_id} failed'
                    )
                self.recipe_id_sequence.pop(0)
        logger.info('No recipe to run or failed to run any recipe')
        return None
