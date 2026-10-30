from module.base.button import ButtonGrid
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


def dock_identity_set(identity):
    """Return unordered identity alternatives, or None for an unrestricted role."""
    if identity is None or identity == 'any':
        return None
    if isinstance(identity, str):
        return {identity}
    return set(identity)


def dock_character_matches(character, identity=None, emotion=None, emotion_limit=None,
                           grade=None, status='free', blacklist=()):
    if identity is not None or blacklist:
        if character.identity in (None, '', 'unknown') or character.identity in blacklist:
            return False
        identities = dock_identity_set(identity)
        if identities is None:
            if character.identity == 'Workerjuu':
                return False
        elif character.identity not in identities:
            return False
    limitations = dict(emotion=emotion, emotion_limit=emotion_limit, grade=grade, status=status)
    for name, value in limitations.items():
        if value is not None and value != 'any' and getattr(character, name) is None:
            return False
        if isinstance(value, (set, frozenset)):
            limitations[name] = list(value)
    return character.satisfy_limitation(limitations)


def dock_grade_key(character):
    return 'SABCDE'.index(character.grade) if character.grade in ('S', 'A', 'B', 'C', 'D', 'E') else 6


class IslandDock(IslandUI):
    def is_in_island_dock(self):
        return self.appear(ISLAND_DOCK_CHECK, offset=(0, 20))

    def handle_island_dock_loading(self):
        for _ in self.loop(timeout=1.5):
            if self.match_template_color(ISLAND_DOCK_CHARACTER_CONFIRM, offset=(0, 20)):
                break

    def _island_dock_quit_check_func(self):
        return not self.appear(ISLAND_DOCK_CHECK, offset=(20, 20))

    def island_dock_quit(self):
        self.ui_back(check_button=self._island_dock_quit_check_func, skip_first_screenshot=True)
        del_cached_property(self, 'dock_grid')

    def island_dock_sort_method_dsc_set(self, enable=True, wait_loading=True):
        if ISLAND_DOCK_SORTING.set('Descending' if enable else 'Ascending', main=self):
            del_cached_property(self, 'dock_grid')
            if wait_loading:
                self.handle_island_dock_loading()

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
        if count >= 3:
            logger.warning(f'Unexpected card count in view: {count}, retrying detection')
            count = 0
        if count > 0:
            y_list = rows[:, 1]
            origin_y = y_list.min() + ISLAND_DOCK_DETECT_AREA[1]
        else:
            logger.warning('No cards detected, retrying detection')
            origin_y = 139

        grid = ButtonGrid(
            origin=(ISLAND_DOCK_DETECT_AREA[0], origin_y),
            delta=ISLAND_DOCK_CARD_DELTA,
            button_shape=ISLAND_DOCK_CARD_SIZE,
            grid_shape=(6, count),
            name='CARD'
        )
        return grid

    def next_dock_page(self, wait_loading=True):
        p1, p2 = random_rectangle_vector_opted((0, -250), box=ISLAND_DOCK_DETECT_AREA, padding=-10)
        self.device.drag(p1, p2, hold_duration=0.1, name='ISLAND_DOCK_NEXT_PAGE_SWIPE')
        del_cached_property(self, 'dock_grid')
        if wait_loading:
            for _ in self.loop(timeout=1.5):
                pass

    def prev_dock_page(self, wait_loading=True):
        p1, p2 = random_rectangle_vector_opted((0, 250), box=ISLAND_DOCK_DETECT_AREA, padding=-10)
        self.device.drag(p1, p2, hold_duration=0.1, name='ISLAND_DOCK_PREV_PAGE_SWIPE')
        del_cached_property(self, 'dock_grid')
        if wait_loading:
            for _ in self.loop(timeout=1.5):
                pass

    def ensure_dock_page_at_top(self):
        ISLAND_DOCK_DETECT.load_color(self.device.image)
        ISLAND_DOCK_DETECT._match_init = True
        drag_count = 0
        for _ in self.loop(timeout=10):
            self.prev_dock_page()
            drag_count += 1
            if self.appear(ISLAND_DOCK_DETECT, offset=(20, 20)):
                if drag_count >= 2:
                    logger.info('Reached top of dock page')
                    return True
            else:
                ISLAND_DOCK_DETECT.load_color(self.device.image)
                drag_count = 0
        return False

    def island_dock_select_one(self, button, skip_first=False):
        """
        Args:
            button (Button): Character button to select
            skip_first (bool):
        """
        for _ in self.loop(skip_first=skip_first, timeout=5):
            if self.is_button_selected(button, color=(19, 181, 231)):
                logger.info(f'Button {button.name} is selected')
                return True
            else:
                if self.appear(ISLAND_DOCK_CHECK, offset=(20, 20), interval=1):
                    self.device.click(button)
                continue
        logger.warning(f'Failed to select dock button {button.name}')
        return False

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

            if self.appear_then_click(ISLAND_DOCK_CHARACTER_CONFIRM, offset=(20, 20), interval=2):
                continue

    def island_dock_scan_page(self, disabled=()):
        """Recognize a live page without hiding occupied or filtered characters."""
        if 'status' in disabled:
            raise ValueError('Dock searches require status recognition')
        characters = []
        for _ in self.loop(timeout=3):
            grid = self.dock_grid
            if not grid.buttons:
                del_cached_property(self, 'dock_grid')
                continue
            scanner = CharacterScanner(grid, identity=None, emotion=None,
                                       emotion_limit=None, grade=None, status=None)
            scanner.disable(*disabled)
            characters = scanner.scan(self.device.image)
            # Leave one card so an entirely unreadable page still retries.
            while len(characters) > 1:
                last = characters[-1]
                if not (last.identity == 'unknown' and last.emotion == 0 and last.emotion_limit == 0):
                    break
                characters.pop()
            if characters and ('identity' in disabled
                               or all(c.identity not in (None, '', 'unknown') for c in characters)):
                break
        return characters

    def island_dock_search(self, handle_page, descending=True, start_at_top=False,
                           timeout=40, disabled=()):
        """Process each live page before scrolling, resetting to the top only when requested.

        A handler returns None to continue, or a result to stop immediately.
        Return (result, completed); incomplete recognition and timeouts cannot
        establish that a requested character is absent. Handlers must click
        current-page buttons before returning None, never cache them for later.
        """
        self.island_dock_sort_method_dsc_set(enable=descending)
        if start_at_top and not self.ensure_dock_page_at_top():
            return None, False
        unchanged = 0
        incomplete = False
        for _ in self.loop(timeout=timeout):
            characters = self.island_dock_scan_page(disabled=disabled)
            if not characters:
                return None, False
            # Page scanning removes empty grid cells only from the bottom tail.
            at_bottom = len(characters) < len(self.dock_grid.buttons)
            if 'identity' not in disabled:
                incomplete |= any(c.identity in (None, '', 'unknown') for c in characters)
            result = handle_page(characters)
            if result is not None:
                return result, True
            if at_bottom:
                return None, not incomplete
            # A selection may have changed highlights since the previous drag.
            ISLAND_DOCK_DETECT.load_color(self.device.image)
            ISLAND_DOCK_DETECT._match_init = True
            self.next_dock_page()
            if self.appear(ISLAND_DOCK_DETECT, offset=(20, 20)):
                unchanged += 1
                if unchanged >= 2:
                    return None, not incomplete
            else:
                unchanged = 0
        return None, False

    def island_dock_select_character(self, identity=None, emotion=None, emotion_limit=None,
                                     grade=None, status='free', blacklist=(), descending=True,
                                     fallback=False, fallback_descending=True, disabled=(),
                                     prefer_grade=False, unavailable=None, start_at_top=False):
        """Search using filters and preferences, then select on the current page.

        Return the selected character after verification, or None on failure.

        Identity recognition is optional when no identity filter, blacklist, or
        unavailable-identity tracking is requested. Grade is read only when
        filtering or ranking by grade.
        Identity collections are unordered alternatives. With fallback enabled,
        try a free character outside these alternatives after they are resolved
        unavailable or reliably absent. All other filters and the blacklist stay
        in force. A timeout or incomplete scan does not prove absence.
        """
        identities = dock_identity_set(identity)
        blacklist = set(blacklist)
        if identity is not None or blacklist or unavailable is not None:
            if 'identity' in disabled:
                raise ValueError('This search requires identity recognition')
        elif 'identity' not in disabled:
            disabled = tuple(disabled) + ('identity',)
        if grade in (None, 'any') and not prefer_grade and 'grade' not in disabled:
            disabled = tuple(disabled) + ('grade',)
        unavailable = set() if unavailable is None else unavailable
        seen = set(blacklist)
        filters = dict(identity=identity if identities is None else identities,
                       emotion=emotion, emotion_limit=emotion_limit,
                       grade=grade, status=status, blacklist=blacklist)

        def match_page(characters):
            unavailable.update(c.identity for c in characters if c.status == 'occupied'
                               and c.identity not in (None, '', 'unknown'))
            if prefer_grade:
                characters = sorted(characters, key=dock_grade_key)
            for character in characters:
                if (character.status == 'free' and dock_character_matches(character, **filters)
                        and not self.is_button_selected(character.button, color=(19, 181, 231))):
                    return character
            seen.update(c.identity for c in characters if c.identity not in (None, '', 'unknown'))
            if identities is not None and identities <= seen:
                return False
            return None

        if identities is not None and identities <= blacklist:
            character, completed = None, True
        else:
            character, completed = self.island_dock_search(
                match_page, descending=descending, start_at_top=start_at_top, disabled=disabled)
            start_at_top = True
        if character:
            if self.island_dock_select_one(character.button):
                return character
            return None
        if fallback and identities is not None and completed:
            return self.island_dock_select_character(
                identity='any', emotion=emotion, emotion_limit=emotion_limit, grade=grade, status='free',
                blacklist=blacklist | identities, descending=fallback_descending,
                disabled=disabled, prefer_grade=prefer_grade, unavailable=unavailable,
                start_at_top=start_at_top)
        return None

    def island_dock_select_workerjuu(self, descending=False):
        """Select Workerjuu from the current page after sorting."""
        def select_page(characters):
            for character in characters:
                if dock_character_matches(character, identity='Workerjuu'):
                    if self.island_dock_select_one(character.button):
                        return character
                    return False
            return False

        character, _ = self.island_dock_search(
            select_page, descending=descending, disabled=('emotion', 'emotion_limit', 'grade'))
        if character:
            return character
        logger.warning('Failed to find Workerjuu in dock')
        return None
