from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Union

import cv2
import numpy as np

import module.config.server as server
from module.base.button import ButtonGrid
from module.base.utils import color_similar, crop, extract_letters, get_color, limit_in, save_image
from module.combat.level import LevelOcr
from module.logger import logger
from module.ocr.ocr import Digit
from module.retire.assets import (TEMPLATE_FLEET_1, TEMPLATE_FLEET_2,
                                  TEMPLATE_FLEET_3, TEMPLATE_FLEET_4,
                                  TEMPLATE_FLEET_5, TEMPLATE_FLEET_6,
                                  TEMPLATE_IN_BATTLE, TEMPLATE_IN_COMMISSION,
                                  TEMPLATE_IN_EVENT_FLEET)
from module.retire.dock import (CARD_EMOTION_GRIDS, CARD_GRIDS,
                                CARD_LEVEL_GRIDS, CARD_RARITY_GRIDS)


class EmotionDigit(Digit):
    def pre_process(self, image):
        if server.server == 'jp':
            image_gray = extract_letters(image, letter=(255, 255, 255), threshold=self.threshold)
            right_side = np.nonzero(image_gray[0:16, :].min(axis=0) > 176)[-1]
            image = image[:, :right_side[-1]]

        image = super().pre_process(image)
        return image

    def after_process(self, result):
        # Random OCR error on Downes' hair
        # OCR DOCK_EMOTION_OCR: Result "044" is revised to "44"
        if result == '044' or result == 'D44':
            result = '0'

        return super().after_process(result)


@dataclass(frozen=True)
class Ship:
    rarity: str = ''
    level: int = 0
    emotion: int = 0
    fleet: int = 0
    status: str = ''
    button: Any = None

    def satisfy_limitation(self, limitaion) -> bool:
        for key in self.__dict__:
            value = limitaion.get(key)
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

        return True


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
        return self.ocr_model.ocr(image)

    def limit_value(self, value) -> int:
        return limit_in(value, 0, 150)


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
        self.value_list: List[str] = ['free', 'battle', 'commission']
        self.templates = {
            TEMPLATE_IN_BATTLE: 'battle',
            TEMPLATE_IN_COMMISSION: 'commission',
            TEMPLATE_IN_EVENT_FLEET: 'in_event_fleet',
        }

    def _match(self, image) -> str:
        for template, status in self.templates.items():
            if template.match(image, similarity=0.75):
                return status

        return 'free'

    def _scan(self, image) -> List:
        image_list = [crop(image, button.area) for button in self.grids.buttons]

        return [self._match(image) for image in image_list]

    def limit_value(self, value) -> str:
        return value if value in self.value_list else 'any'


class ShipScanner(Scanner):
    """
    Ship Scanner is designed to use with an "Initial" page_dock, which means there cannot be
    any move once a dock filter was set. Otherwise, it may return untrustable results.

    If you need to scan rather more than the initial page, Please use DockScanner.

    By default, all properties of the ship are scanned.
    You can set the required properties by calling enable() or disable().
    disable() will simply skip scanning and set those properties to None.
    To keep them and ignore limitations, use set_limitation(property=None)

    Args:
        rarity (str, list): ['any', 'common', 'rare', 'elite', 'super_rare'].
        level (tuple): (lower, upper). Will be limited in range [1, 125]
        emotion (tuple): (lower, upper). Will be limited in range [0, 150]
        fleet (int): 0 means not in any fleet. Will be limited in range [0, 6]
        status (str, list): ['any', 'commission', 'battle']
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
        self.limitaion: Dict[str, Union[str, int, Tuple[int, int]]] = {
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
                button=button)
            for level, emotion, rarity, fleet, status, button in
            zip(
                self.sub_scanners['level'].results,
                self.sub_scanners['emotion'].results,
                self.sub_scanners['rarity'].results,
                self.sub_scanners['fleet'].results,
                self.sub_scanners['status'].results,
                self.grids.buttons)
        ]

        for scanner in self.sub_scanners.values():
            scanner.clear()

        return candidates

    def scan(self, image, cached=False, output=True) -> Union[List, None]:
        ships = super().scan(image, cached, output)
        if not cached:
            return [ship for ship in ships if ship.satisfy_limitation(self.limitaion)]

    def move(self, vector) -> None:
        """
        Apply moving to both sub-scanners and self.
        """
        for scanner in self.sub_scanners.values():
            scanner.move(vector)

        super().move(vector)

    def limit_value(self, key, value) -> None:
        if value is None:
            self.limitaion[key] = None
        elif isinstance(value, tuple):
            lower, upper = value
            lower = self.sub_scanners[key].limit_value(lower)
            upper = self.sub_scanners[key].limit_value(upper)
            self.limitaion[key] = (lower, upper)
        else:
            self.limitaion[key] = self.sub_scanners[key].limit_value(value)

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
            status (str, list): ['any', 'commission', 'battle']
        """
        for attr in self.limitaion.keys():
            value = kwargs.get(attr, self.limitaion[attr])
            self.limit_value(key=attr, value=value)

        logger.info(f'Limitaions set to {self.limitaion}')


class DockScanner(ShipScanner):
    """
    Dock Scanner support multi-page scan.

    Same as ShipScanner, DockScanner must start at the initial page_dock.
    The scanning process can swipe the dock automatically and stop when finished.
    """
    def __init__(self, rarity: str = 'any', level: Tuple[int, int] = (1, 125), emotion: Tuple[int, int] = (0, 150), fleet: int = 0, status: str = 'any') -> None:
        raise NotImplementedError
        super().__init__(rarity, level, emotion, fleet, status)
        self.scan_zone = (93, 76, 1218, 719)
        self.card_bottom = []

    def multi_scan(self, image):
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
        # Roughly Adjust
        # After graying the image, calculate the standard deviation and take the part below the threshold
        # Those parts should present multiple discontinuous subsequences, which here called gap_seq
        scan_image = crop(image, self.scan_zone, copy=False)

        def find_bound(image):
            bound = []
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            std = np.std(image, axis=1)
            gap_seq = [720] + list(np.nonzero(std < 10)[0])
            logger.info(f'{gap_seq}')
            for pos in range(len(gap_seq) - 1, 0, -1):
                if abs(gap_seq[pos - 1] - gap_seq[pos]) > 50:
                    bound.append(gap_seq[pos])
            if len(bound) < 3:
                bound = [0] + bound
            return bound

        bounds = [find_bound(crop(scan_image, button.area, copy=False)) for button in self.scan_grids.buttons]
        card_bottom = (np.mean(bounds, axis=0) + 0.5).astype(np.uint8)
        # Calculate the bound of gap_seq, usually we get 3 endpoints
        # The offset is the difference between the two groups of endpoints
        # Notice the example above, the first endpoint is the closest to the boundary, so we use its difference.
        offset_rough = card_bottom[0] - self.card_bottom[0]
        self.card_bottom.clear()
        self.card_bottom.extend(card_bottom)

        # Preciously Adjust
        # The adjustment here is based on CARD_RARITY_GRIDS, whose height is 5
        # After binarization, the standard deviation of its surroundings is very small
        # A correct offset will place CARD_RARITY_GRIDS on the first 5 lines
        # Now do what similar to rough adjustment can get a precious offset
        # !!!!
        # Pratice shows that, the above method seems to have a poor effect
        # Further work is needed.
        offset = offset_rough
        self.move(offset)

    def scan_one_fleet(self, fleet: int = None) -> List[Ship]:
        """
        Scan all ships in a certain fleet.
        It fleet is not specified, use self.fleet.
        """
        pass

    def scan_whole_dock(self) -> List[Ship]:
        pass
