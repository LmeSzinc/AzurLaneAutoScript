import os
import time
from abc import ABCMeta, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Union

import cv2
import numpy as np

import module.config.server as server
from module.base.button import ButtonGrid
from module.base.utils import (color_similar, crop, extract_letters, get_color,
                               image_color_count, limit_in,
                               random_normal_distribution_int,
                               random_rectangle_point)
from module.combat.level import LevelOcr
from module.logger import logger
from module.ocr.ocr import Digit
from module.retire.assets import (DOCK_CHECK, SHIP_DETAIL_CHECK,
                                  TEMPLATE_FLEET_1, TEMPLATE_FLEET_2,
                                  TEMPLATE_FLEET_3, TEMPLATE_FLEET_4,
                                  TEMPLATE_FLEET_5, TEMPLATE_FLEET_6,
                                  TEMPLATE_IN_BATTLE, TEMPLATE_IN_COMMISSION, TEMPLATE_IN_HARD,
                                  TEMPLATE_IN_EVENT_FLEET)
from module.retire.dock import (CARD_EMOTION_GRIDS, CARD_EMOTION_STATUS_GRIDS, CARD_GRIDS,
                                CARD_LEVEL_GRIDS, CARD_RARITY_GRIDS, DOCK_SCROLL,
                                EMOTION_RED, EMOTION_YELLOW, EMOTION_GREEN)


class EmotionDigit(Digit):
    def pre_process(self, image):
        if server.server == 'jp':
            image_gray = extract_letters(image, letter=(255, 255, 255), threshold=self.threshold)
            right_side = np.nonzero(image_gray[0:16, :].max(axis=0) > 192)[-1]
            for i, col in enumerate(right_side):
                if i < col:
                    break
            image = image[:, :i]
        image = super().pre_process(image)
        return image

    def after_process(self, result):
        # Random OCR error on Downes' hair
        # OCR DOCK_EMOTION_OCR: Result "044" is revised to "44"
        if result == '044' or result == 'D44':
            result = '0'

        result = super().after_process(result)
        if result > 150 and result % 10 in [1, 4]:
            result //= 10

        return result


@dataclass(frozen=True)
class Ship:
    rarity: str = ''
    level: int = 0
    emotion: int = 0
    fleet: int = 0
    status: str = ''
    button: Any = None
    hash_: str = field(default='', repr=False)

    def satisfy_limitation(self, limitation) -> bool:
        for key in self.__dict__:
            value = limitation.get(key)
            if self.__dict__[key] is not None and value is not None:
                # str and int should be exactly equal to
                if isinstance(value, (str, int)):
                    if value == 'any':
                        continue
                    if self.__dict__[key] != value:
                        return False
                # tuple means should be in range
                elif isinstance(value, tuple):
                    if not (value[0] <= self.__dict__[key] <= value[1]):
                        return False
                # list means should be in the list
                elif isinstance(value, list):
                    if self.__dict__[key] not in value:
                        return False

        return True


class DHash:
    EQ_THRES: int = 30

    def __init__(self, image, size=8) -> None:
        self.code = DHash.gen_hash(image, size)

    @staticmethod
    def gen_hash(image, size=8) -> str:
        if len(image.shape) > 2:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        image = cv2.resize(image, (size + 1, size + 1))
        row_diff = np.packbits(image[:-1, :-1] > image[1:, :-1])
        col_diff = np.packbits(image[:-1, :-1] > image[:-1, 1:])
        row_hash: str = ''.join([f'{i:>02x}' for i in row_diff])
        col_hash: str = ''.join([f'{i:>02x}' for i in col_diff])

        return f'{row_hash}{col_hash}'

    @staticmethod
    def distance(__x, __y) -> int:
        if isinstance(__x, DHash) and isinstance(__y, DHash):
            __x, __y = int(__x.code, 16), int(__y.code, 16)
        elif isinstance(__x, str) and isinstance(__y, str):
            __x, __y = int(__x, 16), int(__y, 16)

        return bin(__x ^ __y).count('1')

    def __eq__(self, __o: object) -> bool:
        return type(self) == type(__o) and DHash.distance(self, __o) < DHash.EQ_THRES

    def __repr__(self) -> str:
        return self.code


class Scanner(metaclass=ABCMeta):
    _results: List = None
    _enabled: bool = True
    _disabled_value: List[None] = [None] * 14
    grids: ButtonGrid = None

    @property
    def results(self) -> List:
        return self._results

    @abstractmethod
    def _scan(self, image) -> List:
        pass

    @abstractmethod
    def limit_value(self, value) -> Any:
        pass

    def clear(self) -> None:
        """
        Clear all cached results.
        """
        self._results.clear()

    def scan(self, image, cached=False, output=False) -> Union[List, None]:
        """
        If scanner is enabled, return the real results.
        Otherwise, return a series of None.

        For multi-scan, caching the results is recommended.
        If cached is set, results will be cached.
        """
        results: List = self._scan(image) if self._enabled else self._disabled_value

        if output:
            for result in results:
                logger.info(f'{result}')

        if cached:
            self._results.extend(results)
        else:
            return results

    def move(self, vector) -> None:
        """
        Call ButtonGrid.move for property grids.
        """
        self.grids = self.grids.move(vector)

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False


class LevelScanner(Scanner):
    def __init__(self) -> None:
        super().__init__()
        self._results = []
        self.grids = CARD_LEVEL_GRIDS
        self.ocr_model = LevelOcr(self.grids.buttons,
                                  name='DOCK_LEVEL_OCR', threshold=64)

    def _scan(self, image) -> List:
        return self.ocr_model.ocr(image)

    def limit_value(self, value) -> int:
        return limit_in(value, 1, 125)
    
    def move(self, vector) -> None:
        super().move(vector)
        self.ocr_model.buttons = [button.area for button in self.grids.buttons]


class EmotionScanner(Scanner):
    def __init__(self) -> None:
        super().__init__()
        self._results = []
        self.grids = CARD_EMOTION_GRIDS
        if server.server != 'jp':
            self.ocr_model = EmotionDigit(self.grids.buttons,
                                      name='DOCK_EMOTION_OCR', threshold=176)
        else:
            self.ocr_model = EmotionDigit(self.grids.buttons,
                                      name='DOCK_EMOTION_OCR', 
                                      letter=(201, 201, 201), 
                                      threshold=176)

    def _scan(self, image) -> List:
        results = []
        for emotion, emotion_status in zip(
                self.ocr_model.ocr(image),
                EmotionStatusScanner().scan(image)):
            if emotion_status == 'red':
                emotion = 0
            elif emotion_status == 'yellow':
                if emotion > 30:
                    emotion //= 10
            elif emotion_status == 'green':
                if emotion > 40:
                    emotion //= 10
            results.append(emotion)
        logger.attr('DOCK_EMOTION_OCR', results)
        return results

    def limit_value(self, value) -> int:
        return limit_in(value, 0, 150)

    def move(self, vector) -> None:
        super().move(vector)
        self.ocr_model.buttons = [button.area for button in self.grids.buttons]


class EmotionStatusScanner(Scanner):
    def __init__(self) -> None:
        super().__init__()
        self._results = []
        self.grids = CARD_EMOTION_STATUS_GRIDS
        self.value_list: List[str] = ['red', 'yellow', 'green', 'unknown']

    def get_emotion_status(self, image) -> str:
        """
        Get the emotion status (at the right-up corner of the ship card).
        EmotionStatus can be ['yellow', 'green', 'red', 'unknown'].
            'yellow': 1 <= emotion <= 30
            'green': 31 <= emotion <= 40
            'red': emotion = 0
            'unknown': emotion > 40

        Args:
            image (np.ndarray):

        Returns:
            str: EmotionStatus
        """
        if image_color_count(image, color=EMOTION_YELLOW, count=300):
            return 'yellow'
        elif image_color_count(image, color=EMOTION_GREEN, count=300):
            return 'green'
        elif image_color_count(image, color=EMOTION_RED, count=300):
            return 'red'
        else:
            return 'unknown'

    def _scan(self, image) -> List:
        results = [self.get_emotion_status(crop(image, button.area, copy=False))
                   for button in self.grids.buttons]
        logger.attr('DOCK_EMOTION_STATUS', results)
        return results

    def limit_value(self, value) -> str:
        return value if value in self.value_list else 'any'


class RarityScanner(Scanner):
    def __init__(self) -> None:
        super().__init__()
        self._results = []
        self.grids = CARD_RARITY_GRIDS
        self.value_list: List[str] = ['common', 'rare', 'elite', 'super_rare']

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

    def _scan(self, image) -> List:
        return [self.color_to_rarity(get_color(image, button.area))
                for button in self.grids.buttons]

    def limit_value(self, value) -> str:
        return value if value in self.value_list else 'any'


class FleetScanner(Scanner):
    def __init__(self) -> None:
        super().__init__()
        self._results = []
        self.grids = CARD_GRIDS.crop(area=(0, 117, 35, 162), name='FLEET')
        self.templates = {
            TEMPLATE_FLEET_1: 1,
            TEMPLATE_FLEET_2: 2,
            TEMPLATE_FLEET_3: 3,
            TEMPLATE_FLEET_4: 4,
            TEMPLATE_FLEET_5: 5,
            TEMPLATE_FLEET_6: 6
        }

    def pre_process(self, image):
        """
        Practice shows that, the following steps will lead to a better performance.
        It can distinguish the number from the background very well.
        If anyone needs to update TEMPLATE_FLEET assets, do remember to preprocess
        the image first.
        """
        _, g, _ = cv2.split(image)
        _, image = cv2.threshold(g, 205, 255, cv2.THRESH_BINARY)
        image = cv2.merge([image, image, image])

        return image

    def _match(self, image) -> int:
        """
        Using a template matching method to identify fleet.
        Performance on ultra rarity is not very good, because the flash
        will interfere with identification.
        Assuming it is not in any fleet if none matched.
        """
        for template, fleet in self.templates.items():
            if template.match(image):
                return fleet

        if TEMPLATE_FLEET_1.match(image, similarity=0.80):
            return 1
        elif TEMPLATE_FLEET_3.match(image, similarity=0.80):
            return 3
        elif TEMPLATE_FLEET_4.match(image, similarity=0.80):
            return 4
        else:
            return 0

    def _scan(self, image) -> List:
        image = self.pre_process(image)
        image_list = [crop(image, button.area) for button in self.grids.buttons]

        return [self._match(image) for image in image_list]

    def limit_value(self, value) -> int:
        return limit_in(value, 0, 6)


class StatusScanner(Scanner):
    def __init__(self) -> None:
        super().__init__()
        self._results = []
        self.grids = CARD_GRIDS
        self.value_list: List[str] = [
            'free',
            'battle',
            'commission',
            'in_hard_fleet',
            'in_event_fleet',
        ]
        self.templates = {
            TEMPLATE_IN_BATTLE: 'battle',
            TEMPLATE_IN_COMMISSION: 'commission',
            TEMPLATE_IN_HARD: 'in_hard_fleet',
            TEMPLATE_IN_EVENT_FLEET: 'in_event_fleet',
        }

    def _match(self, image) -> str:
        for template, status in self.templates.items():
            if template.match(image, similarity=0.8):
                return status

        return 'free'

    def _scan(self, image) -> List:
        image_list = [crop(image, button.area) for button in self.grids.buttons]

        return [self._match(image) for image in image_list]

    def limit_value(self, value) -> str:
        return value if value in self.value_list else 'any'


class HashGenerator(Scanner):
    def __init__(self, length=8) -> None:
        super().__init__()
        self._results = []
        self.length = length
        self.grids = CARD_GRIDS

    def _scan(self, image) -> List:
        image_list = [crop(image, button.area) for button in self.grids.buttons]

        return [DHash(image, self.length) for image in image_list]

    def limit_value(self, value) -> Any:
        pass


class ShipScanner(Scanner):
    """
    Ship Scanner is designed to use with an "Initial" page_dock, which means there cannot be
    any move once a dock filter was set. Otherwise, it may return untrustable results.

    If you need to scan rather more than the initial page, Please use DockScanner.

    Args:
        rarity (str, list): ['any', 'common', 'rare', 'elite', 'super_rare'].
        level (tuple): (lower, upper). Will be limited in range [1, 125]
        emotion (tuple): (lower, upper). Will be limited in range [0, 150]
        fleet (int): 0 means not in any fleet. Will be limited in range [0, 6]
        status (str, list): [
            'free',
            'battle',
            'commission',
            'in_hard_fleet',
            'in_event_fleet',
            ]

    By default, all properties of the ship are scanned.
    "False" and "None" are two special values for the properties of ship.

    Using False:
        The scanner will skip scanning by simply setting them to None.
        Doing so will discard the property, assuming you don't care about them.
        Once a property is set to False, it can only be enabled by calling enable().
        And calling disable() has the same effect as using False.

    Using None:
        The scanner will work normally, but ignoring the limitations on them
        when filter the results. set_limitation(property=...) can reset the limitaiions,
        including set them to None.

    Examples:
        ShipScanner(rarity=False) will get a list of ships whose rarity is None.
        This can be used in a situation where rarity is not a concern.
        Then calling ShipScanner.enable('rairty').
    """
    def __init__(
        self,
        rarity: str = 'any',
        level: Tuple[int, int] = (1, 125),
        emotion: Tuple[int, int] = (0, 150),
        fleet: int = 0,
        status: str = 'any'
    ) -> None:
        super().__init__()
        self._results = []
        self.grids = CARD_GRIDS
        self.limitation: Dict[str, Union[str, int, Tuple[int, int]]] = {
            'level': (1, 125),
            'emotion': (0, 150),
            'rarity': 'any',
            'fleet': 0,
            'status': 'any',
        }

        # Each property of a ship must be binded to a Scanner.
        self.sub_scanners: Dict[str, Scanner] = {
            'level': LevelScanner(),
            'emotion': EmotionScanner(),
            'rarity': RarityScanner(),
            'fleet': FleetScanner(),
            'status': StatusScanner(),
            'hash': HashGenerator(),
        }

        self.set_limitation(
            level=level, emotion=emotion, rarity=rarity, fleet=fleet, status=status)

    def _scan(self, image) -> List:
        for scanner in self.sub_scanners.values():
            scanner.scan(image, cached=True)

        candidates: List[Ship] = [
            Ship(
                level=level,
                emotion=emotion,
                rarity=rarity,
                fleet=fleet,
                status=status,
                button=button,
                hash_=hash_)
            for level, emotion, rarity, fleet, status, button, hash_ in
            zip(
                self.sub_scanners['level'].results,
                self.sub_scanners['emotion'].results,
                self.sub_scanners['rarity'].results,
                self.sub_scanners['fleet'].results,
                self.sub_scanners['status'].results,
                self.grids.buttons,
                self.sub_scanners['hash'].results)
        ]

        for scanner in self.sub_scanners.values():
            scanner.clear()

        return candidates

    def scan(self, image, cached=False, output=True) -> Union[List, None]:
        ships = super().scan(image, cached, output)
        if not cached:
            return [ship for ship in ships if ship.satisfy_limitation(self.limitation)]

    def move(self, vector) -> None:
        """
        Apply moving to both sub-scanners and self.
        """
        for scanner in self.sub_scanners.values():
            scanner.move(vector)

        super().move(vector)

    def limit_value(self, key, value) -> None:
        if value is None:
            self.limitation[key] = None
        elif isinstance(value, tuple):
            lower, upper = value
            lower = self.sub_scanners[key].limit_value(lower)
            upper = self.sub_scanners[key].limit_value(upper)
            self.limitation[key] = (lower, upper)
        elif isinstance(value, list):
            self.limitation[key] = [self.sub_scanners[key].limit_value(v) for v in value]
        else:
            self.limitation[key] = self.sub_scanners[key].limit_value(value)

    def enable(self, *args) -> None:
        """
        Enable property sub-scanners.

        Supported properties includes:
            ['level', 'emotion', 'rarity', 'fleet', 'status']
        """
        for name, scanner in self.sub_scanners.items():
            if name in args:
                scanner.enable()

    def disable(self, *args) -> None:
        """
        Disable property sub-scanners.

        Supported properties includes:
            ['level', 'emotion', 'rarity', 'fleet', 'status']
        """
        for name, scanner in self.sub_scanners.items():
            if name in args:
                scanner.disable()

    def set_limitation(self, **kwargs):
        """
        Args:
            rarity (str, list): ['any', 'common', 'rare', 'elite', 'super_rare'].
            level (tuple): (lower, upper). Will be limited in range [1, 125]
            emotion (tuple): (lower, upper). Will be limited in range [0, 150]
            fleet (int): 0 means not in any fleet. Will be limited in range [0, 6]
            status (str, list): [
                'free',
                'battle',
                'commission',
                'in_hard_fleet',
                'in_event_fleet',
                ]
        """
        for attr in self.limitation.keys():
            value = kwargs.get(attr, self.limitation[attr])
            self.limit_value(key=attr, value=value)
            if value is False:
                self.sub_scanners[attr].disable()

        logger.info(f'Limitations set to {self.limitation}')


class DockScanner(ShipScanner):
    """
    Dock Scanner support multi-page scan.

    Same as ShipScanner, DockScanner must start at the initial page_dock.
    The scanning process can swipe the dock automatically and stop when finished.
    """
    SCAN_ZONES: Dict[str, Tuple[int, int, int, int]] = {
        'dock': (93, 55, 1219, 719),
    }
    def __init__(self, zone: str = 'dock', test_name: str = '') -> None:
        self._results = []
        self.scan_zone: Tuple[int, int, int, int] = self.SCAN_ZONES[zone]
        self.zone_top: int = self.scan_zone[1]
        self.zone_height: int = self.scan_zone[3] - self.scan_zone[1]
        self.grids_top: int = 76
        # For reposition and moving
        self.mean_color_set = deque(maxlen=2)
        self.moving_distance: int = 0
        self.bound = []
        # For status
        self._stable: bool = False
        self._no_change: int = 0
        self.last_results = []
        self.retry: int = 0

        self.scanner = ShipScanner(emotion=False, fleet=False, status=False)

        # The following is for the debug
        self.save_debug_info = False
        self.debug_folder = f'./log/dock_scan_test/{test_name}_{int(time.time()*1000):x}'
        if self.save_debug_info:
            if not os.path.exists('./log/dock_scan_test'):
                os.mkdir('./log/dock_scan_test')
            if not os.path.exists(self.debug_folder):
                os.mkdir(self.debug_folder)
        self.debug_info = {
            'time' : 0,
            'ship_count' : 0,
            'dock_size' : 0,
            'ocr_mistake' : 0,
            'reposition_retry' : 0,
        }
        self.ocr_mistake_image = []
        self.extend_log = []
        self.moving_distance_log = []

    def limit_value(self, value) -> Any:
        pass

    @property
    def stable(self) -> bool:
        if self._stable:
            self._stable = False
            return True
        else:
            return False

    @property
    def mean_color(self):
        return self.mean_color_set[-1] if self.mean_color_set else None

    @mean_color.setter
    def mean_color(self, value):
        self.mean_color_set.append(value)

    def no_change(self) -> bool:
        return self._no_change > 3

    def _find_bound(self, image) -> List[int]:
        """
        Roughly Adjust.

        The standard deviation of blank line will show obvious troughs.
        The position of the blank line can be obtained by locating the position
        of the wave troughs. Although it is not accurate, we only need its center.
        """
        image = crop(image, self.scan_zone)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        std = np.std(image, axis=1)
        move_avg = np.convolve(std, np.ones((5, )) / 5, mode='valid')
        gap_seq = list(np.nonzero(move_avg < 20)[0]) + [1000]

        bound = []
        start = 0
        for i in range(len(gap_seq) - 1):
            if gap_seq[i + 1] - gap_seq[i] > 50 and i + 1 - start > 10:
                bound.append(np.mean(gap_seq[start : i + 1]).astype(np.int))
                start = i + 1
        if len(bound) > 1:
            # The last line is not credible
            bound[-1] = min(bound[-2] + 225, bound[-1])

        return bound

    def reset_position(self) -> None:
        offset = 76 - self.grids_top
        self.grids_top += offset
        self.scanner.move((0, offset))
        self.mean_color_set.append(self.mean_color_set[0])

    def reposition(self, image, bound) -> None:
        """
        Preciously Adjust.

        *bound* has given the centers of those blank line.
        Go down from these central points, the first line whose color has a large
        difference from mean_color is the top of the new CARD_GRIDS.
        """
        scan_image = crop(image, self.scan_zone)
        if self.mean_color is not None:
            for y in range(0, 20):
                if not color_similar(np.mean(scan_image[bound[0] + y], axis=0), self.mean_color, 60):
                    break
            offset = y + self.zone_top + bound[0] + 1 - self.grids_top
            self.grids_top += offset
            self.scanner.move((0, offset))

        self.mean_color = np.mean(scan_image[bound[-1]], axis=0)

    def _remove_duplicate(self, results) -> int:
        """
        There are two kinds of duplicate in results.
            Two lines:
                The new result is exactly the same as the last one.
            One lines.
                The first line of new result is ths same as the last line of the old one.
        In both cases, len(results) < 14 means reaching the bottom.
        """
        if self._results:
            if all([old.hash_ == new.hash_ for new, old in zip(results, self._results[-len(results):])]):
                self._no_change += 999 if len(results) < 14 else 1
                return 0
            elif all([old.hash_ == new.hash_ for new, old in zip(results[:7], self._results[-7:])]):
                self._results.extend(results[7-len(results):])
                self._no_change = 999 if len(results) < 14 else 0
                return len(results)-7

        self._no_change = 0
        self._results.extend(results)
        return len(results)

    def ensure_in_dock(self, main) -> None:
        if main.appear(SHIP_DETAIL_CHECK, offset=(30, 30)):
            main.ui_back(DOCK_CHECK)

    def _scan(self, image) -> None:
        bound = self._find_bound(image)
        if len(bound) == 1:
            # No ship appears
            self._stable = True
            return
        elif len(bound) == 2:
            if self.bound != bound:
                self._stable = False
                self.bound = bound
                return
        else:
            self.bound.clear()

        self.moving_distance = bound[-1] - (self.zone_height - 204 * 2 - 23 * 3) / 2 * 1.5
        self.moving_distance_log.append(self.moving_distance)
        self.reposition(image, bound)
        results = self.scanner.scan(image, cached=False, output=False)
        if not results:
            self.retry += 1
            self.debug_info['reposition_retry'] += 1
            logger.info(f'No ship was detected, reset the position. Retry {self.retry} time(s)')
            self.reset_position()
            self.reposition(image, bound)
            results = self.scanner.scan(image, cached=False, output=False)
            if self.retry > 3:
                self.moving_distance = random_normal_distribution_int(10, 20)
                self.retry = 0
        else:
            self.retry = 0

        if all([old.hash_ == new.hash_ for new, old in zip(results, self.last_results)]):
            self._stable = True
            inc = self._remove_duplicate(results)
            if inc:
                level = [ship.level for ship in results]
                self.extend_log.append((inc, self.grids_top, level, cv2.cvtColor(image, cv2.COLOR_BGR2RGB)))

                level = [ship.level for ship in results]
                greater_equal = [level[i-1] >= level[i] for i in range(1, len(level))]
                in_order = all(x == greater_equal[0] for x in greater_equal)
                if not in_order:
                    interrupt = np.where(np.array(greater_equal)==False)[0].tolist()
                    values = [level[i] for i in interrupt]
                    level_info = '_'.join([f'{p,v}' for p,v in zip(interrupt,values)])
                    self.ocr_mistake_image.append((
                        f"{self.debug_info['ocr_mistake']}_{self.grids_top}_{level_info}.png", cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    ))
                    self.debug_info['ocr_mistake'] += 1

        self.last_results = results

    def multi_scan(self, main) -> None:
        """
        Here is a simple example,
            □ | □ | □                          --------- (*)
            ---------                          ■ | □ | □
            □ | □ | □       --- Moving --->    ---------
            --------- (*)                      □ | □ | □
            ■ | □ | □                          ---------
        □ and ■ is a ship, | and - is the blank between ships.
        To detect the moving above, we need to know the distance
        that (*) moves.

        There is little color change in the blanks between ships.
        Therefore, graying the image and filter by np.std can get
        the position of those blanks.
        """
        from module.retire.enhancement import OCR_DOCK_AMOUNT
        self.debug_info['dock_size'], _, _ = OCR_DOCK_AMOUNT.ocr(main.device.image)

        if DOCK_SCROLL.appear(main):
            # can partly pre-load the image of ships,
            # which reduce the possibility of getting stuck
            DOCK_SCROLL.set_bottom(main)
            DOCK_SCROLL.set_top(main)

        start_time = time.time()
        while True:
            while not self.stable:
                main.device.screenshot()
                self.ensure_in_dock(main)
                self._scan(main.device.image)

            click_zone_index = random_normal_distribution_int(0, 6)
            start = random_rectangle_point((
                240 + click_zone_index * 165, 555, 250 + click_zone_index * 165, 719
            ))
            end = (start[0], start[1] - self.moving_distance)
            sharp_end = (end[0] - 165, end[1])
            main.device.swipe(start, end)
            main.device.click_record.pop()
            main.device.swipe(end, sharp_end)
            main.device.click_record.pop()

            if not DOCK_SCROLL.appear(main) or (DOCK_SCROLL.at_bottom(main) and self.no_change()):
                break
        end_time = time.time()
        self.debug_info['time'] = end_time - start_time
        self.debug_info['ship_count'] = len(self._results)

        if self.save_debug_info:
            # save hash sims
            hashs = [ship.hash_ for ship in self.results]
            sims = []
            for i in range(len(hashs)):
                for j in range(i+1, len(hashs)):
                    sims.append(DHash.distance(hashs[i],hashs[j]))
            np.save(f'{self.debug_folder}/{len(sims)}.npy', np.array(sims))
            # save ocr mistake
            for name, image in self.ocr_mistake_image:
                cv2.imwrite(f'{self.debug_folder}/{name}.png', image)
            # save another ocr mistake
            self.extend_log.append((0, None))
            for i in range(len(self.extend_log) - 1):
                cnt, top, level, image = self.extend_log[i]
                if cnt != 14 and cnt != 7 and self.extend_log[i+1][0] != 0:
                    cv2.imwrite(f'{self.debug_folder}/len={cnt}_top={top}_id={i}.png', image)
                    self.debug_info[f'len={cnt}_top={top}_id={i}'] = level
            # save debug info
            self.debug_info['moving_mean'] = np.mean(self.moving_distance_log)
            with open(f'{self.debug_folder}/debug_info.txt', 'w', encoding='utf-8') as f:
                for k,v in self.debug_info.items():
                    f.write(f'{k} = {v}\n')

            logger.info(f'debug info has been saved in {self.debug_folder}')

    def scan(self, image, cached=False, output=True) -> Union[List, None]:
        """
        Please use multi_scan() instead.
        """
        pass

    def scan_one_fleet(self, fleet: int = None) -> List[Ship]:
        """
        Scan all ships in a certain fleet.
        It fleet is not specified, use self.fleet.
        """
        pass

    def scan_whole_dock(self) -> List[Ship]:
        pass
