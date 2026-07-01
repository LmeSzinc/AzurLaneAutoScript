from module.base.button import Button, ButtonGrid
from module.base.decorator import cached_property, del_cached_property
from module.base.utils import random_rectangle_vector_opted
from module.island.ui import IslandUI
from module.island_handler.assets import *
from module.island_handler.dock_scanner import CharacterScanner
from module.logger import logger
from module.map_detection.utils import Points
from module.ui.switch import Switch

ISLAND_DOCK_SORTING = Switch('island_dock_sorting')
ISLAND_DOCK_SORTING.add_state('Ascending', check_button=ISLAND_DOCK_SORT_ASC,
                              click_button=ISLAND_DOCK_SORTING_CLICK, offset=(20, 5))
ISLAND_DOCK_SORTING.add_state('Descending', check_button=ISLAND_DOCK_SORT_DESC,
                              click_button=ISLAND_DOCK_SORTING_CLICK, offset=(20, 5))
ISLAND_DOCK_DETECT_AREA = (56, 128, 880, 561)
ISLAND_DOCK_DETECT = Button(ISLAND_DOCK_DETECT_AREA, color=(), button=ISLAND_DOCK_DETECT_AREA, name='ISLAND_DOCK_DETECT')
ISLAND_DOCK_CARD_ANCHOR_AREA = (11, 9, 29, 27)
ISLAND_DOCK_CARD_DELTA = (140, 180)
ISLAND_DOCK_CARD_SIZE = (124, 164)

class IslandDock(IslandUI):
    def is_in_island_dock(self):
        return self.appear(ISLAND_DOCK_CHECK, offset=(0, 20))

    def handle_island_dock_loading(self):
        for _ in self.loop(timeout=1.2):
            pass

    def _island_dock_quit_check_func(self):
        return not self.appear(ISLAND_DOCK_CHECK, offset=(20, 20))

    def island_dock_quit(self):
        self.ui_back(check_button=self._island_dock_quit_check_func, skip_first_screenshot=True)

    def island_dock_sort_method_dsc_set(self, enable=True, wait_loading=True):
        """
        Args:
            enable (bool): True to set descending sorting
            wait_loading (bool): Default to True, use False on continuous operation
        """
        if ISLAND_DOCK_SORTING.set('Descending' if enable else 'Ascending', main=self):
            if wait_loading:
                self.handle_island_dock_loading()
            return True
        return False

    def _get_dock_buttons(self):
        area = (ISLAND_DOCK_DETECT_AREA[0] + ISLAND_DOCK_CARD_ANCHOR_AREA[0],
                ISLAND_DOCK_DETECT_AREA[1] + ISLAND_DOCK_CARD_ANCHOR_AREA[1],
                ISLAND_DOCK_DETECT_AREA[2] - ISLAND_DOCK_CARD_SIZE[0] + ISLAND_DOCK_CARD_ANCHOR_AREA[2],
                ISLAND_DOCK_DETECT_AREA[3] - ISLAND_DOCK_CARD_SIZE[1] + ISLAND_DOCK_CARD_ANCHOR_AREA[3])
        image = self.image_crop(area, copy=True)
        anchors = TEMPLATE_ISLAND_DOCK_CARD_ANCHOR.match_multi(image, threshold=5)
        logger.attr('cards_in_view', len(anchors))
        rows = Points([(0., a.area[1]) for a in anchors]).group(threshold=5)
        return rows

    @cached_property
    def dock_grid(self):
        for _ in self.loop(timeout=2):
            grid = self.get_dock_grid()
            if len(grid.buttons) >= 6:
                return grid
        return grid

    def get_dock_grid(self):
        rows = self._get_dock_buttons()
        count = len(rows)
        delta_y = ISLAND_DOCK_CARD_DELTA[1]
        if count >= 3:
            logger.warning(f'Unexpected card count in view: {count}, assume 2 rows')
            count = 2
        if count > 0:
            y_list = rows[:, 1]
            origin_y = y_list.min() + ISLAND_DOCK_DETECT_AREA[1]
        else:
            logger.warning('No cards detected, use default position')
            origin_y = 139
            count = 2

        grid = ButtonGrid(
            origin=(ISLAND_DOCK_DETECT_AREA[0], origin_y),
            delta=ISLAND_DOCK_CARD_DELTA,
            button_shape=ISLAND_DOCK_CARD_SIZE,
            grid_shape=(6, count),
            name='CARD'
        )
        return grid

    def next_dock_page(self):
        p1, p2 = random_rectangle_vector_opted((0, -250), box=ISLAND_DOCK_DETECT_AREA, padding=-10)
        self.device.drag(p1, p2, hold_duration=0.1, name='ISLAND_DOCK_NEXT_PAGE_SWIPE')
        del_cached_property(self, 'dock_grid')
        self.device.screenshot()

    def prev_dock_page(self):
        p1, p2 = random_rectangle_vector_opted((0, 250), box=ISLAND_DOCK_DETECT_AREA, padding=-10)
        self.device.drag(p1, p2, hold_duration=0.1, name='ISLAND_DOCK_PREV_PAGE_SWIPE')
        del_cached_property(self, 'dock_grid')
        self.device.screenshot()

    def ensure_dock_page_at_top(self):
        ISLAND_DOCK_DETECT.load_color(self.device.image)
        ISLAND_DOCK_DETECT._match_init = True
        for _ in self.loop(timeout=10):
            self.prev_dock_page()
            if self.appear(ISLAND_DOCK_DETECT, offset=(20, 20)):
                logger.warning('Reached top of dock page')
                return True
            else:
                ISLAND_DOCK_DETECT.load_color(self.device.image)
        return False

    def island_dock_select_one(self, button, skip_first=True):
        """
        Args:
            button (Button): Character button to select
            skip_first (bool):
        """
        self.interval_clear(ISLAND_DOCK_CHECK)
        for _ in self.loop(skip_first=skip_first):
            if self.is_button_selected(button, color=(19, 181, 231)):
                break

            if self.appear(ISLAND_DOCK_CHECK, offset=(20, 20), interval=5):
                self.device.click(button)
                continue

    def island_dock_select_confirm(self, check_button, skip_first=True):
        """
        Args:
            check_button (callable, Button):
            skip_first (bool):
        """
        for _ in self.loop(skip_first=skip_first):
            if self.ui_process_check_button(check_button):
                del_cached_property(self, 'dock_grid')
                break

            if self.appear_then_click(ISLAND_DOCK_CHARACTER_CONFIRM, offset=(20, 20), interval=5):
                continue

    def island_dock_select_manjuu(self):
        self.island_dock_sort_method_dsc_set(enable=False)
        scanner = CharacterScanner(self.dock_grid, identity=['Manjuu'], status='free')
        candidates = scanner.scan(self.device.image)
        if candidates:
            self.island_dock_select_one(candidates[0].button)
            return True
        else:
            logger.warning('No Manjuu found in dock')
            return False

    def island_dock_find_character(self, identity):
        self.island_dock_sort_method_dsc_set(enable=True)
        ISLAND_DOCK_DETECT.load_color(self.device.image)
        ISLAND_DOCK_DETECT._match_init = True
        for _ in self.loop(timeout=40, skip_first=False):
            scanner = CharacterScanner(self.dock_grid, identity=identity, status=None)
            candidates = scanner.scan(self.device.image)
            for candidate in candidates:
                if candidate.identity != identity:
                    continue
                return candidate
            self.next_dock_page()
            if self.appear(ISLAND_DOCK_DETECT, offset=(20, 20)):
                logger.warning('Reached end of dock page')
                break
            else:
                ISLAND_DOCK_DETECT.load_color(self.device.image)
        else:
            logger.warning('Failed to find all requested characters')
            return None

    def island_dock_select_character_with_blacklist(self, blacklist):
        self.island_dock_sort_method_dsc_set(enable=True)
        ISLAND_DOCK_DETECT.load_color(self.device.image)
        ISLAND_DOCK_DETECT._match_init = True
        for _ in self.loop(timeout=40, skip_first=False):
            scanner = CharacterScanner(self.dock_grid, identity='any', status='free')
            candidates = scanner.scan(self.device.image)
            candidates = (
                [c for c in candidates if c.grade == 'S']
                + [c for c in candidates if c.grade == 'A']
                + [c for c in candidates if c.grade == 'B']
                + [c for c in candidates if c.grade == 'C']
                + [c for c in candidates if c.grade == 'D']
                + [c for c in candidates if c.grade == 'E']
            )
            for candidate in candidates:
                if candidate.identity in blacklist:
                    logger.warning(f'Candidate {candidate.identity} is in blacklist, skip')
                    continue
                elif self.is_button_selected(candidate.button, color=(19, 181, 231)):
                    continue
                else:
                    self.island_dock_select_one(candidate.button)
                    return candidate.identity
            self.next_dock_page()
            if self.appear(ISLAND_DOCK_DETECT, offset=(20, 20)):
                logger.warning('Reached end of dock page')
                break
            else:
                ISLAND_DOCK_DETECT.load_color(self.device.image)
        logger.warning('Failed to find any character not in blacklist')
        return None