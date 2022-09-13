from dataclasses import dataclass
from typing import Any, Dict, Tuple, Union

from module.base.button import ButtonGrid
from module.equipment.equipment import Equipment
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from module.retire.assets import *
from module.ui.scroll import Scroll
from module.ui.switch import Switch

from ..base.utils import color_similar, crop, get_color, limit_in
from ..combat.level import LevelOcr
from module.retire.fleet import FleetClassifier

DOCK_SORTING = Switch('Dork_sorting')
DOCK_SORTING.add_status('Ascending', check_button=SORT_ASC, click_button=SORTING_CLICK)
DOCK_SORTING.add_status('Descending', check_button=SORT_DESC, click_button=SORTING_CLICK)

DOCK_FAVOURITE = Switch('Favourite_filter')
DOCK_FAVOURITE.add_status('on', check_button=COMMON_SHIP_FILTER_ENABLE)
DOCK_FAVOURITE.add_status('off', check_button=COMMON_SHIP_FILTER_DISABLE)

FILTER_SORT_GRIDS = ButtonGrid(
    origin=(284, 60), delta=(158, 0), button_shape=(137, 38), grid_shape=(6, 1), name='FILTER_SORT')
FILTER_SORT_TYPES = [
    ['rarity', 'level', 'total', 'join', 'intimacy', 'stat']]  # stat has extra grid, not worth pursuing

FILTER_INDEX_GRIDS = ButtonGrid(
    origin=(284, 133), delta=(158, 57), button_shape=(137, 38), grid_shape=(6, 2), name='FILTER_INDEX')
FILTER_INDEX_TYPES = [['all', 'vanguard', 'main', 'dd', 'cl', 'ca'],
                      ['bb', 'cv', 'repair', 'ss', 'others', 'not_available']]

FILTER_FACTION_GRIDS = ButtonGrid(
    origin=(284, 267), delta=(158, 57), button_shape=(137, 38), grid_shape=(6, 2), name='FILTER_FACTION')
FILTER_FACTION_TYPES = [['all', 'eagle', 'royal', 'sakura', 'iron', 'dragon'],
                        ['sardegna', 'northern', 'iris', 'vichya', 'other', 'not_available']]

FILTER_RARITY_GRIDS = ButtonGrid(
    origin=(284, 400), delta=(158, 0), button_shape=(137, 38), grid_shape=(6, 1), name='FILTER_RARITY')
FILTER_RARITY_TYPES = [['all', 'common', 'rare', 'elite', 'super_rare', 'ultra']]

FILTER_EXTRA_GRIDS = ButtonGrid(
    origin=(284, 473), delta=(158, 57), button_shape=(137, 38), grid_shape=(6, 2), name='FILTER_EXTRA')
FILTER_EXTRA_TYPES = [['no_limit', 'has_skin', 'can_retrofit', 'enhanceable', 'can_limit_break', 'not_level_max'],
                      ['can_awaken', 'can_awaken_plus', 'special', 'oath_skin', 'not_available', 'not_available']]

CARD_GRIDS = ButtonGrid(
    origin=(93, 76), delta=(164 + 2 / 3, 227), button_shape=(138, 204), grid_shape=(7, 2), name='CARD')
CARD_RARITY_GRIDS = CARD_GRIDS.crop(area=(0, 0, 138, 5), name='RARITY')
CARD_LEVEL_GRIDS = CARD_GRIDS.crop(area=(77, 5, 138, 27), name='LEVEL')
CARD_EMOTION_GRIDS = CARD_GRIDS.crop(area=(23, 29, 48, 52), name='EMOTION')

CARD_BOTTOM_GRIDS = CARD_GRIDS.move(vector=(0, 94), name='CARD')
CARD_BOTTOM_LEVEL_GRIDS = CARD_LEVEL_GRIDS.move(vector=(0, 94), name='LEVEL')
CARD_BOTTOM_EMOTION_GRIDS = CARD_EMOTION_GRIDS.move(vector=(0, 94), name='EMOTION')

DOCK_SCROLL = Scroll(DOCK_SCROLL, color=(247, 211, 66), name='DOCK_SCROLL')

OCR_DOCK_SELECTED = DigitCounter(DOCK_SELECTED, threshold=64, name='OCR_DOCK_SELECTED')


class Dock(Equipment):
    def handle_dock_cards_loading(self):
        # Poor implementation.
        self.device.sleep((1, 1.5))
        self.device.screenshot()

    def dock_favourite_set(self, enable=False):
        if DOCK_FAVOURITE.set('on' if enable else 'off', main=self):
            self.handle_dock_cards_loading()

    def _dock_quit_check_func(self):
        return not self.appear(DOCK_CHECK, offset=(20, 20))

    def dock_quit(self):
        self.ui_back(check_button=self._dock_quit_check_func, skip_first_screenshot=True)

    def dock_sort_method_dsc_set(self, enable=True):
        if DOCK_SORTING.set('Descending' if enable else 'Ascending', main=self):
            self.handle_dock_cards_loading()

    def dock_filter_enter(self):
        self.ui_click(DOCK_FILTER, appear_button=DOCK_CHECK, check_button=DOCK_FILTER_CONFIRM,
                      skip_first_screenshot=True)

    def dock_filter_confirm(self):
        self.ui_click(DOCK_FILTER_CONFIRM, check_button=DOCK_CHECK, skip_first_screenshot=True)
        self.handle_dock_cards_loading()

    def dock_filter_set_execute(self, sort='level', index='all', faction='all', rarity='all', extra='no_limit',
                                skip_first_screenshot=True):
        """
        A faster filter set function.

        Args:
            sort (str, list):
            index (str, list):
            faction (str, list):
            rarity (str, list):
            extra (str, list):
            skip_first_screenshot:

        Returns:
            bool: If success.

        Pages:
            in: DOCK_FILTER_CONFIRM
        """
        # [[button_1, need_enable_1], ...]
        list_filter = []
        for category in ['sort', 'index', 'faction', 'rarity', 'extra']:
            require = locals()[category]
            require = require if isinstance(require, list) else [require]
            grids = globals()[f'FILTER_{category.upper()}_GRIDS']
            names = globals()[f'FILTER_{category.upper()}_TYPES']
            for x, y, button in grids.generate():
                name = names[y][x]
                list_filter.append([button, name in require])

        for _ in range(5):
            logger.info(
                f'Setting dock filter, sort={sort}, index={index}, faction={faction}, rarity={rarity}, extra={extra}')
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            change_count = 0
            for button, enable in list_filter:
                active = self.image_color_count(button, color=(181, 142, 90), threshold=235, count=250) \
                         or self.image_color_count(button, color=(74, 117, 189), threshold=235, count=250)
                if enable and not active:
                    self.device.click(button)
                    self.device.sleep((0.1, 0.2))
                    change_count += 1

            # End
            if change_count == 0:
                return True

        logger.warning('Failed to set all dock filters after 5 trial, assuming current filters are correct.')
        return False

    def dock_filter_set(self, sort='level', index='all', faction='all', rarity='all', extra='no_limit'):
        """
        A faster filter set function.

        Args:
            sort (str, list): ['rarity', 'level', 'total', 'join', 'intimacy', 'stat']
            index (str, list): [['all', 'vanguard', 'main', 'dd', 'cl', 'ca'],
                                ['bb', 'cv', 'repair', 'ss', 'others', 'not_available']]
            faction (str, list): [['all', 'eagle', 'royal', 'sakura', 'iron', 'dragon'],
                                  ['sardegna', 'northern', 'iris', 'vichya', 'other', 'not_available']]
            rarity (str, list): [['all', 'common', 'rare', 'elite', 'super_rare', 'ultra']]
            extra (str, list): [['no_limit', 'has_skin', 'can_retrofit', 'enhanceable', 'can_limit_break', 'not_level_max'],
                                ['can_awaken', 'can_awaken_plus', 'special', 'oath_skin', 'not_available', 'not_available']]

        Pages:
            in: page_dock
        """
        self.dock_filter_enter()
        self.dock_filter_set_execute()  # Reset filter
        self.dock_filter_set_execute(sort=sort, index=index, faction=faction, rarity=rarity, extra=extra)
        self.dock_filter_confirm()

    def dock_select_one(self, button, skip_first_screenshot=True):
        """
        Args:
            button (Button): Ship button to select
            skip_first_screenshot:
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.dock_selected():
                break

            if self.appear(DOCK_CHECK, interval=5):
                self.device.click(button)
                continue
            if self.handle_popup_confirm('DOCK_SELECT'):
                continue

    def dock_selected(self):
        current, _, _ = OCR_DOCK_SELECTED.ocr(self.device.image)
        return current > 0

    def dock_select_confirm(self, check_button, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(check_button, offset=(30, 30)):
                break

            if self.appear_then_click(SHIP_CONFIRM, offset=(200, 50), interval=5):
                continue
            if self.handle_popup_confirm('DOCK_SELECT_CONFIRM'):
                continue


@dataclass(frozen=True)
class Ship:
    rarity: str = ''
    level: int = 0
    emotion: int = 0
    fleet: int = 0
    in_commission: bool = False
    button: Any = None

    def satisfy_limitation(self, limitaion) -> bool:
        for key in self.__dict__:
            value = limitaion.get(key)
            if value is not None:
                # str, int or bool should be exactly equal to
                if isinstance(value, (str, int, bool)):
                    if self.__dict__[key] != value:
                        return False
                # tuple means should be in range
                elif isinstance(value, tuple):
                    if not (value[0] <= self.__dict__[key] <= value[1]):
                        return False

        return True


class DockScanner:
    def __init__(
        self,
        rarity: Union[str, None] = None,
        level: Tuple[int, int] = (1, 125),
        emotion: Tuple[int, int] = (0, 150),
        fleet: int = 0,
        in_commission: bool = False
    ) -> None:
        """
        Args:
            rarity (str, list): ['common', 'rare', 'elite', 'super_rare']. None for unrestricted.
            level (tuple): (lower, upper). Will be limited in range [1, 125]
            emotion (tuple): (lower, upper). Will be limited in range [0, 150]
            fleet (int): 0 means not in any fleet. Will be limited in range [0, 6]
            in_commission (bool):
        """
        self.limitaion: Dict[str, Union[str, int, Tuple[int, int]]] = {}

        lower: int = limit_in(level[0], 1, 125)
        upper: int = limit_in(level[1], 1, 125)
        self.limitaion['level'] = (lower, upper)

        lower: int = limit_in(emotion[0], 0, 150)
        upper: int = limit_in(emotion[1], 0, 150)
        self.limitaion['emotion'] = (lower, upper)

        rarity = rarity if rarity in ['common', 'rare', 'elite', 'super_rare'] else None
        self.limitaion['rarity'] = rarity

        self.limitaion['fleet'] = (0, 6) if fleet is None else limit_in(fleet, 0, 6)

        self.limitaion['in_commission'] = in_commission

        logger.info(f'Limitaions set to {self.limitaion}')

    def color_to_rarity(self, color: Tuple[int, int, int]) -> str:
        """
        Convert color to a ship rarity.
        Rarity can be ['common', 'rare', 'elite', 'super_rare', 'unknown']
        For 'ultra', color difference is too great,
        thus it's marked as 'unknown'

        Args:
            color (tuple): (r, g, b)

        Returns:
            str: Rarity
        """
        if color_similar(color, (171, 174, 186)):
            return 'common'
        elif color_similar(color, (106, 194, 248)):
            return 'rare'
        elif color_similar(color, (151, 134, 254)):
            return 'elite'
        elif color_similar(color, (247, 221, 101)):
            return 'super_rare'
        else:
            # Difference between ultra is too great
            return 'unknown'

    def scan(self, image) -> None:
        level_ocr = LevelOcr(CARD_LEVEL_GRIDS.buttons,
                             name='DOCK_LEVEL_OCR', threshold=64)
        list_level = level_ocr.ocr(image)

        emotion_ocr = Digit(CARD_EMOTION_GRIDS.buttons,
                            name='DOCK_EMOTION_OCR', threshold=176)
        list_emotion = emotion_ocr.ocr(image)

        list_rarity = [self.color_to_rarity(get_color(image, button.area))
                       for button in CARD_RARITY_GRIDS.buttons]

        fleet_classifier = FleetClassifier(CARD_GRIDS.buttons)
        list_fleet = fleet_classifier.scan(image)

        list_commission = [TEMPLATE_IN_COMMISSION.match(
            crop(image, button.area)) for button in CARD_GRIDS.buttons]

        candidates: list[Ship] = [
            Ship(
                level=level,
                emotion=emotion,
                rarity=rarity,
                fleet=fleet,
                in_commission=in_commission,
                button=button)
            for level, emotion, rarity, fleet, in_commission, button in
            list(zip(
                list_level,
                list_emotion,
                list_rarity,
                list_fleet,
                list_commission,
                CARD_GRIDS.buttons))
        ]

        candidates = [ship for ship in candidates if ship.satisfy_limitation(self.limitaion)]
        logger.info('Ships meeting limitations are:')
        for ship in candidates:
            logger.info(f'{ship}')

        return candidates
