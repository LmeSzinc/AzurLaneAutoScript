from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.equipment.assets import *
from module.logger import logger
from module.storage.storage import StorageHandler
from module.ui.navbar import Navbar
from module.ui.switch import Switch

equipping_filter = Switch('Equiping_filter')
equipping_filter.add_status('on', check_button=EQUIPPING_ON)
equipping_filter.add_status('off', check_button=EQUIPPING_OFF)

SWIPE_DISTANCE = 250
SWIPE_RANDOM_RANGE = (-40, -20, 40, 20)


class Equipment(StorageHandler):
    equipment_has_take_on = False

    def equipping_set(self, enable=False):
        if equipping_filter.set('on' if enable else 'off', main=self):
            self.wait_until_stable(SWIPE_AREA)

    def _equip_view_swipe(self, distance, check_button=EQUIPMENT_OPEN):
        swipe_count = 0
        swipe_timer = Timer(5, count=10)
        self.ensure_no_info_bar(timeout=3)
        SWIPE_CHECK.load_color(self.device.image)
        SWIPE_CHECK._match_init = True  # Disable ensure_template() on match(), allows ship to be properly determined
        # whether actually different or not
        while 1:
            if not swipe_timer.started() or swipe_timer.reached():
                swipe_timer.reset()
                self.device.swipe_vector(vector=(distance, 0), box=SWIPE_AREA.area, random_range=SWIPE_RANDOM_RANGE,
                                         padding=0, duration=(0.1, 0.12), name='EQUIP_SWIPE')
                self.wait_until_appear(check_button, offset=(30, 30))
                swipe_count += 1

            self.device.screenshot()
            if SWIPE_CHECK.match(self.device.image):
                if swipe_count > 1:
                    logger.info('Same ship on multiple swipes')
                    return False
                continue

            if self.appear(check_button, offset=(30, 30)) and not SWIPE_CHECK.match(self.device.image):
                logger.info('New ship detected on swipe')
                return True

    def equip_view_next(self, check_button=EQUIPMENT_OPEN):
        return self._equip_view_swipe(distance=-SWIPE_DISTANCE, check_button=check_button)

    def equip_view_prev(self, check_button=EQUIPMENT_OPEN):
        return self._equip_view_swipe(distance=SWIPE_DISTANCE, check_button=check_button)

    def equip_enter(self, click_button, check_button=EQUIPMENT_OPEN, long_click=True):
        enter_timer = Timer(10)

        while 1:
            if enter_timer.reached():
                if long_click:
                    self.device.long_click(click_button, duration=(1.5, 1.7))
                else:
                    self.device.click(click_button)
                enter_timer.reset()

            self.device.screenshot()

            # End
            if self.appear(check_button):
                break

    @cached_property
    def _equip_side_navbar(self):
        """
        pry_sidebar 3 options
            research.
            equipment.
            detail.

        regular_sidebar 4 options
            enhancement.
            limit break.
            equipment.
            detail.

        retrofit_sidebar 5 options
            retrofit.
            enhancement.
            limit break.
            equipment.
            detail.
        """
        equip_side_navbar = ButtonGrid(
            origin=(21, 118), delta=(0, 94.5), button_shape=(60, 75), grid_shape=(1, 5), name='DETAIL_SIDE_NAVBAR')

        return Navbar(grids=equip_side_navbar,
                      active_color=(247, 255, 173), active_threshold=221,
                      inactive_color=(140, 162, 181), inactive_threshold=221)

    def equip_side_navbar_ensure(self, upper=None, bottom=None):
        """
        Ensure able to transition to page
        Whether page has completely loaded is handled
        separately and optionally

        Args:
            upper (int):
                pry|regular|retrofit
                1|N/A|N/A for research.
                N/A|N/A|1 for retrofit.
                N/A|1|2   for enhancement.
                N/A|2|3   for limit break.
                2|3|4     for equipment.
                3|4|5     for detail.
            bottom (int):
                pry|regular|retrofit
                3|N/A|N/A for research.
                N/A|N/A|5 for retrofit.
                N/A|4|4   for enhancement.
                N/A|3|3   for limit break.
                2         for equipment.
                1         for detail.

        Returns:
            bool: if side_navbar set ensured
        """
        if self._equip_side_navbar.get_total(main=self) == 3:
            if upper == 1 or bottom == 3:
                logger.warning('Transitions to "research" is not supported')
                return False

        if self._equip_side_navbar.set(self, upper=upper, bottom=bottom):
            return True
        return False

    def _equip_take_off_one(self):
        bar_timer = Timer(5)
        off_timer = Timer(5)
        confirm_timer = Timer(5)

        while 1:
            self.device.screenshot()
            if bar_timer.reached() and not self.appear(EQUIP_1, offset=10):
                self.device.click(EQUIPMENT_OPEN)
                bar_timer.reset()
                continue

            if off_timer.reached() and not self.info_bar_count() and self.appear_then_click(EQUIP_OFF, offset=10):
                off_timer.reset()
                continue

            if confirm_timer.reached() and self.handle_popup_confirm():
                confirm_timer.reset()
                continue
            if self.handle_storage_full():
                continue

            # End
            # if self.handle_info_bar():
            #     break
            if off_timer.started() and self.info_bar_count():
                break

    def equipment_take_off(self, enter, out, fleet):
        """
        Args:
            enter (Button): Long click to edit equipment.
            out (Button): Button to confirm exit success.
            fleet (list[int]): list of equipment record. [3, 1, 1, 1, 1, 1]
        """
        logger.hr('Equipment take off')
        self.equip_enter(enter)

        for index in '9'.join([str(x) for x in fleet if x > 0]):
            index = int(index)
            if index == 9:
                self.equip_view_next()
            else:
                self._equip_take_off_one()
                self.ui_click(click_button=EQUIPMENT_CLOSE, check_button=EQUIPMENT_OPEN, offset=None)

        self.ui_back(out)
        self.equipment_has_take_on = False

    def _equip_take_on_one(self, index):
        bar_timer = Timer(5)
        on_timer = Timer(5)

        while 1:
            self.device.screenshot()

            if bar_timer.reached() and not self.appear(EQUIP_1, offset=10):
                self.device.click(EQUIPMENT_OPEN)
                # self.device.sleep(0.3)
                bar_timer.reset()
                continue

            if on_timer.reached() and self.appear(EQUIP_1, offset=10) and not self.info_bar_count():
                if index == 1:
                    self.device.click(EQUIP_1)
                elif index == 2:
                    self.device.click(EQUIP_2)
                elif index == 3:
                    self.device.click(EQUIP_3)

                on_timer.reset()
                continue

            # End
            # if self.handle_info_bar():
            #     break
            if on_timer.started() and self.info_bar_count():
                break

    def equipment_take_on(self, enter, out, fleet):
        """
        Args:
            enter (Button): Long click to edit equipment.
            out (Button): Button to confirm exit success.
            fleet (list[int]): list of equipment record. [3, 1, 1, 1, 1, 1]
        """
        logger.hr('Equipment take on')
        self.equip_enter(enter)

        for index in '9'.join([str(x) for x in fleet if x > 0]):
            index = int(index)
            if index == 9:
                self.equip_view_next()
            else:
                self._equip_take_on_one(index=index)
                self.ui_click(click_button=EQUIPMENT_CLOSE, check_button=EQUIPMENT_OPEN, offset=None)

        self.ui_back(out)
        self.equipment_has_take_on = True
