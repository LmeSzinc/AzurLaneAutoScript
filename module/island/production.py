from datetime import datetime

from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property, has_cached_property
from module.base.timer import Timer
from module.base.utils import random_rectangle_vector_opted
from module.exception import RequestHumanTakeover
from module.island.assets import *
from module.island.data import DIC_ISLAND_PRODUCTION_PLACE, DIC_ISLAND_SLOT
from module.island.utils import item_name_with_id, production_place_name_with_id
from module.island_handler.dock import IslandDock
from module.island_handler.exchange import FISH_MEAT_SOURCES
from module.island_handler.recipe import IslandProductionRestart, IslandRecipe
from module.island_handler.restaurant_config import (
    RESTAURANT_IDS,
    get_selected_named_waitresses,
    get_waitress_slots,
)
from module.logger import logger
from module.map_detection.utils import Points
from module.ui.page import page_island, page_island_manage


ANCHOR_AREA = (452, 7, 481, 36)
DETECT_AREA = (192, 69, 1221, 653)
NAME_AREA = (0, 0, 265, 39)
TAB_SIZE = (490, 159)
TAB_DELTA = (539, 183.5)
SLOT_ORIGIN = (62, 59)
SLOT_SIZE = (86, 86)
SLOT_DELTA = (95 - 1/3, 0)
TICK_AREA = (30, 35, 52, 51)
CHARACTER_SELECT_TITLE_AREA = (515, 144, 765, 202)


def production_slot_name_with_id(slot_id):
    place_id = DIC_ISLAND_SLOT[slot_id]['place']
    return f'{production_place_name_with_id(place_id)} slot {slot_id}'


class IslandProduction(IslandRecipe, IslandDock):
    slot_finish_time = {}
    human_workers_available = True
    _first_run = True
    # main menu related methods
    def _get_tabs(self):
        area = (DETECT_AREA[0] + ANCHOR_AREA[0], DETECT_AREA[1] + ANCHOR_AREA[1], DETECT_AREA[2] - TAB_SIZE[0] + ANCHOR_AREA[2], DETECT_AREA[3] - TAB_SIZE[1] + ANCHOR_AREA[3])
        image = self.image_crop(area, copy=True)
        anchors = TEMPLATE_ISLAND_PRODUCTION_ANCHOR_ICON.match_multi(image, similarity=0.92, threshold=5)
        logger.attr('Production_tabs', len(anchors))
        rows = Points([(0., a.area[1]) for a in anchors]).group(threshold=5)
        return rows

    @cached_property
    def production_grid(self):
        for _ in self.loop(timeout=6):
            grid = self.get_production_grid()
            if len(grid.buttons) >= 4:
                return grid
        return grid

    def get_production_grid(self):
        rows = self._get_tabs()
        count = len(rows)
        if count < 2:
            logger.warning('Unable to find enough production tab anchors, assume tabs are at top')
            origin_y = 70
            delta_y = TAB_DELTA[1]
        elif count < 4:
            y_list = rows[:, 1]
            y1, y2 = y_list[0], y_list[-1]
            origin_y = min(y1, y2) + DETECT_AREA[1]
            delta_y = TAB_DELTA[1]
        else:
            logger.warning(f'Unexpected production tab anchor match result: {[a for a in rows]}')
            origin_y = 70
            delta_y = TAB_DELTA[1]

        production_grid = ButtonGrid(
            origin=(192, origin_y), delta=(TAB_DELTA[0], delta_y), button_shape=TAB_SIZE,
            grid_shape=(2, count), name='PRODUCTION_GRID'
        )
        return production_grid

    @cached_property
    def production_names(self):
        return self.get_production_codename()

    def get_production_codename(self):
        template_to_codename = {
            TEMPLATE_ISLAND_PRODUCTION_FIELD: 101,
            TEMPLATE_ISLAND_PRODUCTION_RANCH: 102,
            TEMPLATE_ISLAND_PRODUCTION_FISHERY: 201,
            TEMPLATE_ISLAND_PRODUCTION_MINE: 401,
            TEMPLATE_ISLAND_PRODUCTION_WOOD: 402,
            TEMPLATE_ISLAND_PRODUCTION_ORCHARD: 501,
            TEMPLATE_ISLAND_PRODUCTION_NURSERY: 502,
            TEMPLATE_ISLAND_PRODUCTION_KOI: 601,
            TEMPLATE_ISLAND_PRODUCTION_BEAR: 602,
            TEMPLATE_ISLAND_PRODUCTION_EATERY: 603,
            TEMPLATE_ISLAND_PRODUCTION_GRILL: 604,
            TEMPLATE_ISLAND_PRODUCTION_LUMBER: 703,
            TEMPLATE_ISLAND_PRODUCTION_MACHINERY: 704,
            TEMPLATE_ISLAND_PRODUCTION_ELECTRONIC: 705,
            TEMPLATE_ISLAND_PRODUCTION_CRAFTS: 706,
            TEMPLATE_ISLAND_PRODUCTION_CAFE: 901,
        }
        name_grid = self.production_grid.crop(NAME_AREA, name='PRODUCTION_NAME_GRID')
        name_images = [self.image_crop(button.area, copy=True) for button in name_grid.buttons]
        codenames = []
        for image in name_images:
            for template, codename in template_to_codename.items():
                if template.match(image):
                    codenames.append(codename)
                    break
            else:
                logger.warning('Failed to recognize production name')
                codenames.append(None)
        places = [
            production_place_name_with_id(place_id)
            if place_id in DIC_ISLAND_PRODUCTION_PLACE else f'Unknown ({place_id})'
            for place_id in codenames
        ]
        logger.attr('Codenames', codenames)
        logger.attr('Production_places', places)
        return codenames

    @cached_property
    def slot_grids(self):
        return self.get_production_slot_grids()

    def get_production_slot_grids(self):
        slot_grids = {}
        names = self.production_names
        for codename, button in zip(names, self.production_grid.buttons):
            if codename not in DIC_ISLAND_PRODUCTION_PLACE:
                logger.warning(f'Codename {codename} not found in DIC_ISLAND_PRODUCTION_PLACE, skip slot grid creation')
                continue
            slot_length = len(DIC_ISLAND_PRODUCTION_PLACE[codename]['slot'])
            slot_grid = ButtonGrid(
                origin=(button.area[0] + SLOT_ORIGIN[0], button.area[1] + SLOT_ORIGIN[1]), delta=SLOT_DELTA, button_shape=SLOT_SIZE,
                grid_shape=(slot_length, 1), name=f'{codename}_SLOT_GRID'
            )
            slot_grids[codename] = slot_grid
        return slot_grids

    def is_slot_finished(self, slot_button: Button):
        tick_button = slot_button.crop(area=TICK_AREA, name=f'{slot_button.name}_TICK')
        return self.image_color_count(tick_button, (255, 255, 255), threshold=15, count=85)

    def is_slot_empty(self, slot_button: Button):
        image = self.image_crop(slot_button.area, copy=True)
        return TEMPLATE_ISLAND_PRODUCTION_SLOT_EMPTY.match(image)

    def next_page(self):
        if 901 in self.production_names:
            logger.info('Already at last page, cannot swipe to next page')
            return False
        p1, p2 = random_rectangle_vector_opted((0, -450), box=(690, 70, 720, 650), padding=0)
        self.device.drag(p1, p2, hold_duration=0.1, name='PRODUCTION_NEXT_PAGE_SWIPE')
        del_cached_property(self, 'production_grid')
        del_cached_property(self, 'production_names')
        del_cached_property(self, 'slot_grids')
        for _ in self.loop(timeout=1):
            if self.handle_island_additional():
                break
        return True

    def prev_page(self):
        if 101 in self.production_names:
            logger.info('Already at first page, cannot swipe to previous page')
            return False
        p1, p2 = random_rectangle_vector_opted((0, 450), box=(690, 70, 720, 650), padding=0)
        self.device.drag(p1, p2, name='PRODUCTION_PREV_PAGE_SWIPE')
        del_cached_property(self, 'production_grid')
        del_cached_property(self, 'production_names')
        del_cached_property(self, 'slot_grids')
        for _ in self.loop(timeout=1):
            if self.handle_island_additional():
                break
        return True

    def ensure_top_page(self):
        for _ in self.loop():
            if 101 in self.production_names:
                break
            if not self.prev_page():
                break
        self.device.click_record_clear()

    def is_enter_window_shown(self):
        return self.image_color_count(CHARACTER_SELECT_TITLE_AREA, (62, 193, 255), threshold=30, count=6000)

    def claim_slot_reward(self, slot_button: Button):
        if not self.is_slot_finished(slot_button):
            logger.warning(f'Slot {slot_button} is not finished, cannot receive reward')
            return False
        for _ in self.loop(timeout=4):
            if self.handle_island_additional():
                continue
            if self.appear_then_click(ISLAND_PRODUCTION_RECEIVE, offset=(120, 20), interval=2):
                continue
            if self.ui_page_appear(page_island_manage, interval=2) and not self.is_enter_window_shown():
                self.device.click(slot_button)
                continue
            if self.is_enter_window_shown() and self.appear(ISLAND_PRODUCTION_SELECT_CHARACTER, offset=(60, 20)):
                break
        for _ in self.loop():
            if self.handle_island_additional():
                continue
            if self.is_enter_window_shown() or self.appear(ISLAND_PRODUCTION_RERUN, offset=(20, 20)):
                self.device.click(ISLAND_CLICK_SAFE_AREA)
                continue
            if self.match_template_color(page_island_manage.check_button) and not self.is_enter_window_shown() and not self.appear(ISLAND_PRODUCTION_SELECT_CHARACTER, offset=(60, 20)):
                return True

    def claim_reward_in_page(self, finished_slots=[]):
        for place_id, slot_grid in self.slot_grids.items():
            for slot_id, slot_button in zip(DIC_ISLAND_PRODUCTION_PLACE[place_id]['slot'], slot_grid.buttons):
                if self.is_slot_finished(slot_button) or self.slot_finish_time.get(slot_id, datetime.max) <= datetime.now():
                    if self.claim_slot_reward(slot_button):
                        self.claimed_slots.add(slot_id)
                    if slot_id in self.slot_finish_time:
                        del self.slot_finish_time[slot_id]

    def claim_all_rewards(self):
        logger.hr("Claim Production Rewards", level=2)
        self.claimed_slots = set()
        self.ensure_top_page()
        while 1:
            self.claim_reward_in_page()
            if not self.next_page():
                break

    def dispatch_slot(self, slot_id, slot_button):
        if slot_id in DIC_ISLAND_PRODUCTION_PLACE[102]['slot']:
            del_cached_property(super(), 'recipe_id_sequence')
            del_cached_property(super(), 'all_recipe_stocks')
        for _ in self.loop():
            if self.is_in_island_dock():
                break
            if self.appear_then_click(ISLAND_PRODUCTION_SELECT_CHARACTER, offset=(60, 20), interval=1):
                continue
            if self.match_template_color(page_island_manage.check_button, interval=1) and not self.is_enter_window_shown():
                self.device.click(slot_button)
                continue
        if self.config.IslandProduction_UseWorkerjuuByDefault or not self.human_workers_available:
            worker = self.island_dock_select_workerjuu()
        else:
            blacklist = set()
            for restaurant_id in RESTAURANT_IDS:
                blacklist.update(get_selected_named_waitresses(get_waitress_slots(self.config, restaurant_id)))
            worker = self.island_dock_select_character(
                emotion=(100, 150), emotion_limit=(100, 149),
                blacklist=blacklist, descending=False)
            if not worker:
                self.device.click_record_remove('ISLAND_DOCK_NEXT_PAGE_SWIPE')
                self.human_workers_available = False
                logger.warning(
                    f'No available character for {production_slot_name_with_id(slot_id)}, '
                    'use Workerjuu for the remaining production slots'
                )
                worker = self.island_dock_select_workerjuu(descending=True)
        if not worker:
            logger.warning(f'Failed to select a worker for {production_slot_name_with_id(slot_id)}')
            self.island_dock_quit()
            return False
        emotion = float('inf') if worker.identity == 'Workerjuu' else worker.emotion
        logger.attr('Worker emotion', emotion)
        self.island_dock_select_confirm(self.is_in_recipe_menu)
        target_time = super().run(slot_id=slot_id, emotion=emotion)
        if target_time is not None:
            target_time = target_time.replace(microsecond=0)
            self.slot_finish_time[slot_id] = target_time
            self.ensure_island_production_page()
        else:
            logger.warning(f'Failed to start production for {production_slot_name_with_id(slot_id)}')
            if slot_id in [9031, 9032, 9033, 9034]:
                del_cached_property(super(), 'recipe_id_sequence')
                del_cached_property(super(), 'all_recipe_stocks')
            self.ui_back(check_button=page_island_manage.check_button)
            self.ensure_island_production_page()
            return False

    def dispatch_place(self, place_id, slots_to_check=None):
        if place_id not in self.slot_grids:
            place = (
                production_place_name_with_id(place_id)
                if place_id in DIC_ISLAND_PRODUCTION_PLACE else f'Unknown production place ({place_id})'
            )
            logger.error(f'{place} not found in current production page')
            return False
        place = production_place_name_with_id(place_id)
        if slots_to_check is not None and not slots_to_check.intersection(
                DIC_ISLAND_PRODUCTION_PLACE[place_id]['slot']):
            logger.info(f'Skip {place}: no new ingredients from completed production')
            return
        logger.info(f'Dispatch production place: {place}')
        slot_grid = self.slot_grids[place_id]
        is_first = True
        for slot_id, slot_button in zip(DIC_ISLAND_PRODUCTION_PLACE[place_id]['slot'], slot_grid.buttons):
            if slots_to_check is not None and slot_id not in slots_to_check:
                continue
            # Ranch slots each have a different recipe.
            if (not is_first and place_id != 102
                    and has_cached_property(super(), 'recipe_id_sequence') and not self.recipe_id_sequence):
                logger.info(f'No more recipe for {place}, skip remaining slots')
                break
            if self.is_slot_empty(slot_button):
                self.dispatch_slot(slot_id=slot_id, slot_button=slot_button)
            if is_first:
                is_first = False
        del_cached_property(super(), 'recipe_id_sequence')
        del_cached_property(super(), 'all_recipe_stocks')

    def dispatch_all(self, check_all_empty_slots=False):
        logger.hr("Dispatch Production", level=2)
        self.human_workers_available = True
        slots_to_check = None
        if not check_all_empty_slots:
            slots_to_check = self.claimed_slots | {
                slot_id for slot_id, slot in DIC_ISLAND_SLOT.items()
                if self.claimed_slots.intersection(slot['ingredient_source_slots'])
            }
            if not slots_to_check:
                logger.info('No completed production or external rewards to retry empty slots')
                return
        self.ensure_top_page()
        self.failed_buy_items = set()
        dispatched_places = set()
        while 1:
            try:
                for place_id in self.slot_grids.keys():
                    if place_id not in dispatched_places:
                        self.dispatch_place(place_id, slots_to_check=slots_to_check)
                        dispatched_places.add(place_id)
                if not self.next_page():
                    break
            except IslandProductionRestart as e:
                if not e.success:
                    self.failed_buy_items.add(e.item_id)
                    logger.warning(
                        f'Failed to acquire ingredient {item_name_with_id(e.item_id)}; '
                        'restart production and skip further attempts for this item'
                    )
                else:
                    logger.info(
                        f'Acquired ingredient {item_name_with_id(e.item_id)}; '
                        'restart production from current page'
                    )
                del_cached_property(self, 'production_grid')
                del_cached_property(self, 'production_names')
                del_cached_property(self, 'slot_grids')
                continue

    def ensure_island_production_page(self):
        self.ui_ensure(page_island_manage)
        for _ in self.loop(timeout=10):
            if self.handle_island_additional():
                continue
            if self.ui_page_appear(page_island_manage, offset=(0, 20)):
                break
        self.island_manage_side_navbar_ensure(upper=1, skip_first_screenshot=False)
        for _ in self.loop():
            rows = self._get_tabs()
            count = len(rows)
            if count >= 2:
                break

    def exchange_surplus_fish(self):
        """
        Exchange fish above their hard floor, reserve and task target into fish meat,
        which holds more PT, and record the fish meat stock for fish production.
        """
        logger.hr("Exchange Surplus Fish", level=2)
        self.ui_goto_island_shop()
        keep = self.get_fish_keep_items()
        for meat_id in FISH_MEAT_SOURCES:
            result = self.island_exchange_fish_meat(meat_id, keep=keep)
            if result is not None:
                self.fish_meat_stock[meat_id] = result.after
        self.ui_back(check_button=page_island.check_button)
        self.ensure_island_production_page()

    def run(self):
        self.ensure_island_production_page()
        slot_finish_time = self.config.cross_get("IslandProduction.Storage.Storage.SlotFinishTime", default={})
        self.slot_finish_time = {int(k): datetime.fromisoformat(v) for k, v in slot_finish_time.items()}
        self.fish_meat_stock = {}
        check_all_empty_slots = self.config.cross_get(
            "IslandProduction.Storage.Storage.CheckAllEmptySlots", default=False)
        # Keep a full check pending until this run's claims and dispatch finish.
        if not check_all_empty_slots:
            self.config.cross_set("IslandProduction.Storage.Storage.CheckAllEmptySlots", True)
        check_all_empty_slots = check_all_empty_slots or IslandProduction._first_run
        self.claim_all_rewards()
        yaml_text = self.config.cross_get("IslandProduction.IslandProduction.DailyBufferItems", "")
        if not yaml_text or yaml_text == "{}":
            logger.critical('No daily buffer items found in config, please run Island Production Planner first')
            raise RequestHumanTakeover('No daily buffer items found in config, please run Island Production Planner first')
        if self.claimed_slots.intersection(DIC_ISLAND_PRODUCTION_PLACE[201]['slot']):
            self.exchange_surplus_fish()
        self.dispatch_all(check_all_empty_slots=check_all_empty_slots)
        next_run_time = list(self.slot_finish_time.values())
        with self.config.multi_set():
            sorted_items = sorted(self.slot_finish_time.items(), key=lambda kv: (kv[1], kv[0]))
            slot_finish_time = {k: v.isoformat(sep=' ') for k, v in sorted_items}
            self.config.cross_set("IslandProduction.Storage.Storage.SlotFinishTime", slot_finish_time)
            self.config.cross_set("IslandProduction.Storage.Storage.CheckAllEmptySlots", False)
            if next_run_time:
                self.config.task_delay(target=next_run_time)
            else:
                self.config.task_delay(minute=30)
        IslandProduction._first_run = False
