from datetime import datetime, timedelta

from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property
from module.config.utils import get_server_next_update
from module.island.assets import *
from module.island_handler.restaurant import IslandRestaurant, WaitressOccupied
from module.logger import logger
from module.ocr.ocr import Duration
from module.ui.page import page_island_manage


BUSINESS_DETECT_AREA = (210, 72, 1203, 685)
BUSINESS_ENTRANCE_AREA = (794, 84, 950, 120)


class IslandBusiness(IslandRestaurant):
    @cached_property
    def skip_restaurant(self):
        open = {
            601: self.has_waitress("IslandBusiness.IslandRestaurant.KoiWaitress", 'none'),
            602: self.has_waitress("IslandBusiness.IslandRestaurant.BearWaitress", 'none'),
            603: self.has_waitress("IslandBusiness.IslandRestaurant.EateryWaitress", 'none'),
            604: self.has_waitress("IslandBusiness.IslandRestaurant.GrillWaitress", 'none'),
            901: self.has_waitress("IslandBusiness.IslandRestaurant.CafeWaitress", 'none')
        }
        return open

    @property
    def business_grid(self):
        return ButtonGrid(
            origin=(210, 88),
            delta=(0, 177),
            button_shape=(993, 161),
            grid_shape=(1, 3),
            name="BUSINESS_GRID"
        )

    @property
    def business_grid_shifted(self):
        return ButtonGrid(
            origin=(210, 168),
            delta=(0, 177),
            button_shape=(993, 161),
            grid_shape=(1, 3),
            name="BUSINESS_GRID_SHIFTED"
        )

    def handle_restaurant_popup(self):
        for _ in self.loop(timeout=5):
            if self.appear(ISLAND_BUSINESS_EVENT_POPUP, offset=(50, 50), interval=1):
                self.device.click(ISLAND_CLICK_SAFE_AREA)
                continue
            if self.appear_then_click(ISLAND_BUSINESS_EVENT_POPUP_CANCEL, offset=(20, 20)):
                continue
            # End
            if self.match_template_color(page_island_manage.check_button, offset=(20, 20)):
                return True

    def restaurant_swipe_to_top(self):
        self.device.swipe_vector((0, 500), box=BUSINESS_DETECT_AREA, padding=-20)
        for _ in self.loop(timeout=0.8):
            pass
        self.shifted = False
        self.index = 0

    def restaurant_swipe_to_bottom(self):
        self.device.swipe_vector((0, -500), box=BUSINESS_DETECT_AREA, padding=-20)
        for _ in self.loop(timeout=0.8):
            pass
        self.shifted = True
        self.index = 1

    def get_restaurant_id(self, button):
        template_to_id = {
            TEMPLATE_ISLAND_BUSINESS_KOI: 601,
            TEMPLATE_ISLAND_BUSINESS_BEAR: 602,
            TEMPLATE_ISLAND_BUSINESS_EATERY: 603,
            TEMPLATE_ISLAND_BUSINESS_GRILL: 604,
            TEMPLATE_ISLAND_BUSINESS_CAFE: 901
        }
        for _ in self.loop(timeout=4):
            image = self.image_crop(button, copy=True)
            for template, id in template_to_id.items():
                if template.match(image):
                    return id
        else:
            logger.warning("Failed to recognize restaurant")
        return None

    def is_restaurant_running(self, button):
        return TEMPLATE_ISLAND_BUSINESS_RUNNING.match(self.image_crop(button, copy=True))

    def is_restaurant_resting(self, button):
        return TEMPLATE_ISLAND_BUSINESS_RESTING.match(self.image_crop(button, copy=True))

    def get_remain_time(self, button):
        time_button = button.crop((851, 11, 913, 38))
        ocr = Duration(time_button, name="RESTAURANT_REMAIN_TIME")
        remain_time = ocr.ocr(self.device.image)
        return remain_time

    index = None
    shifted = None

    def current_restaurant_button(self):
        if self.shifted:
            buttons = self.business_grid_shifted.buttons
        else:
            buttons = self.business_grid.buttons
        if self.index >= len(buttons):
            return None
        return buttons[self.index]

    def next_restaurant(self):
        self.index += 1
        if self.index >= len(self.business_grid.buttons) and not self.shifted:
            self.restaurant_swipe_to_bottom()
        elif self.index >= len(self.business_grid_shifted.buttons) and self.shifted:
            logger.info("No more restaurants")

    def run(self):
        self.ui_ensure(page_island_manage)
        self.island_manage_side_navbar_ensure(upper=2)
        self.handle_restaurant_popup()
        self.restaurant_swipe_to_top()
        unchecked_restaurants = [601, 602, 603, 604, 901]
        next_run_time = {
            601: get_server_next_update('00:00') if not self.skip_restaurant[601] else datetime.now() + timedelta(days=3),
            602: get_server_next_update('00:00') if not self.skip_restaurant[602] else datetime.now() + timedelta(days=3),
            603: get_server_next_update('00:00') if not self.skip_restaurant[603] else datetime.now() + timedelta(days=3),
            604: get_server_next_update('00:00') if not self.skip_restaurant[604] else datetime.now() + timedelta(days=3),
            901: get_server_next_update('00:00') if not self.skip_restaurant[901] else datetime.now() + timedelta(days=3)
        }
        while unchecked_restaurants:
            button = self.current_restaurant_button()
            if button is None:
                logger.warning(f"Restaurant index exhausted, unchecked restaurants: {unchecked_restaurants}")
                break
            restaurant_id = self.get_restaurant_id(button)
            if restaurant_id is None:
                logger.warning("Unrecognized restaurant, should check assets")
                self.next_restaurant()
                continue
            if restaurant_id not in unchecked_restaurants:
                self.next_restaurant()
                continue
            entrance_button = button.crop(BUSINESS_ENTRANCE_AREA)
            if self.skip_restaurant[restaurant_id]:
                logger.info(f"Skip restaurant {restaurant_id}")
                unchecked_restaurants.remove(restaurant_id)
                self.next_restaurant()
                continue
            if self.is_restaurant_running(entrance_button):
                remain_time = self.get_remain_time(button)
                next_run_time[restaurant_id] = datetime.now() + remain_time if remain_time else "Unknown"
                logger.info(f"Restaurant {restaurant_id} is running")
                unchecked_restaurants.remove(restaurant_id)
                self.next_restaurant()
                continue
            if self.is_restaurant_resting(entrance_button):
                logger.info(f"Restaurant {restaurant_id} is resting")
                unchecked_restaurants.remove(restaurant_id)
                self.next_restaurant()
                continue
            logger.info(f"Restaurant {restaurant_id} is ready")
            for _ in self.loop():
                if self.appear(page_island_manage.check_button, offset=(20, 20), interval=1):
                    self.device.click(entrance_button)
                    continue
                if self.is_in_island_restaurant():
                    break
            self.working_restaurant_id = restaurant_id
            try:
                success = super().run()
            except WaitressOccupied:
                next_run_time[restaurant_id] = datetime.now() + timedelta(hours=8)
                unchecked_restaurants.remove(restaurant_id)
                success = False
            self.ui_back(page_island_manage.check_button)
            for _ in self.loop(timeout=0.8, skip_first=False):
                if self.appear(page_island_manage.check_button, offset=(0, 20)):
                    break
            del_cached_property(super(), 'restaurant_has_event')
            del_cached_property(super(), '_restaurant_offset_x')
            del_cached_property(super(), 'restaurant_grid')
            del_cached_property(super(), 'event_buff')
            del_cached_property(super(), '_restaurant_offset')
            if restaurant_id in unchecked_restaurants:
                unchecked_restaurants.remove(restaurant_id)
            if success:
                next_run_time[restaurant_id] = datetime.now() + timedelta(hours=8)
                # Since dealt restaurants will be moved to the bottom,
                # we can directly check the next one without swiping
        self.config.task_delay(target=min(next_run_time.values()))
