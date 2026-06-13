import re
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Union

import cv2

from module.base.button import ButtonGrid
from module.base.utils import color_similarity_2d, crop, limit_in, load_image
from module.island_handler.assets import *
from module.logger import logger
from module.ocr.ocr import Ocr
from module.statistics.utils import load_folder

ISLAND_DOCK_CARD_GRIDS = ButtonGrid(
    origin=(56, 139), delta=(140, 180), button_shape=(124, 164), grid_shape=(6, 2), name='CARD'
)


@dataclass(frozen=True)
class Character:
    identity: str = ''
    emotion: int = 0
    emotion_limit: int = 0
    grade: str = ''
    status: str = ''
    button: Any = None

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
                # list means should be in list
                elif isinstance(value, list):
                    if self.__dict__[key] not in value:
                        return False
        return True


class IslandEmotionCounterOcr(Ocr):
    def __init__(self, buttons, lang='azur_lane', letter=(255, 255, 255), threshold=128, alphabet='0123456789/IDSB',
                 name=None):
        super().__init__(buttons, lang=lang, letter=letter, threshold=threshold, alphabet=alphabet, name=name)

    def pre_process(self, image, background_color_main=(18, 209, 183), background_color_sub=(207, 207, 207)):
        mask = color_similarity_2d(image, background_color_sub)
        mask2 = color_similarity_2d(image, self.letter)
        mask[mask < mask2] = 0
        cv2.inRange(mask, 221, 255, dst=mask)
        image[mask > 0] = background_color_main
        return super().pre_process(image)

    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('I', '1').replace('D', '0').replace('S', '5')
        result = result.replace('B', '8')
        result = re.search(r'(\d+)/(\d+)', result)
        if result:
            result = [int(s) for s in result.groups()]
            current, total = int(result[0]), int(result[1])
            current = min(current, total)
            return current, total - current, total
        else:
            logger.warning(f'Unexpected ocr result: {result}')
            return 0, 0, 0


class Scanner(metaclass=ABCMeta):
    _results: List = None
    _enabled: bool = True
    _disabled_value: List[None] = [None] * 12
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


class IdentityScanner(Scanner):
    def __init__(self, grids: ButtonGrid) -> None:
        super().__init__()
        self._results = []
        self.grids = grids
        self.templates = {}
        data = load_folder('./assets/island/character/')
        for name, image in data.items():
            self.templates[name] = load_image(image)

    def _match(self, image) -> str:
        for name, template_image in self.templates.items():
            res = cv2.matchTemplate(image, template_image, cv2.TM_CCOEFF_NORMED)
            _, sim, _, _ = cv2.minMaxLoc(res)
            if sim > 0.75:
                return name
        return 'unknown'

    def _scan(self, image) -> List:
        image_list = [crop(image, button.area) for button in self.grids.buttons]
        return [self._match(image) for image in image_list]

    def limit_value(self, value) -> str:
        return value if value in self.templates.keys() else 'any'


class EmotionCounterScanner(Scanner):
    def __init__(self, grids: ButtonGrid) -> None:
        super().__init__()
        self._results = []
        self.grids = grids.crop((7, 141, 59, 154), name='EMOTION')
        self.ocr_model = IslandEmotionCounterOcr(self.grids.buttons, name='EMOTION_COUNTER_OCR')

    def _scan(self, image) -> List:
        return self.ocr_model.ocr(image)


class EmotionScanner(EmotionCounterScanner):
    def _scan(self, image) -> List:
        results = super()._scan(image)
        return [result[0] for result in results]

    def limit_value(self, value):
        if value == 999:
            return 999
        return limit_in(value, 0, 150)


class EmotionLimitScanner(EmotionCounterScanner):
    def _scan(self, image) -> List:
        results = super()._scan(image)
        return [result[2] for result in results]

    def limit_value(self, value):
        if value == 999:
            return 999
        return limit_in(value, 100, 150)


class GradeScanner(Scanner):
    def __init__(self, grids: ButtonGrid) -> None:
        super().__init__()
        self._results = []
        self.grids = grids.crop((98, 138, 117, 157), name='GRADE')
        self.templates = {
            # TEMPLATE_ISLAND_DOCK_GRADE_S: 'S',
            TEMPLATE_ISLAND_DOCK_GRADE_A: 'A',
            TEMPLATE_ISLAND_DOCK_GRADE_B: 'B',
            TEMPLATE_ISLAND_DOCK_GRADE_C: 'C',
            TEMPLATE_ISLAND_DOCK_GRADE_D: 'D',
            TEMPLATE_ISLAND_DOCK_GRADE_E: 'E',
        }

    def _match(self, image) -> str:
        for template, grade in self.templates.items():
            if template.match(image, similarity=0.95):
                return grade
        return 'unknown'

    def _scan(self, image) -> List:
        image_list = [crop(image, button.area) for button in self.grids.buttons]
        return [self._match(image) for image in image_list]

    def limit_value(self, value) -> str:
        return value if value in self.templates.values() else 'any'


class StatusScanner(Scanner):
    def __init__(self, grids: ButtonGrid) -> None:
        super().__init__()
        self._results = []
        self.grids = grids
        self.value_list: List[str] = ['free', 'occupied']
        self.templates = {
            TEMPLATE_ISLAND_DOCK_OCCUPIED: 'occupied'
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


class CharacterScanner(Scanner):
    """
    CharacterScanner is designed to use with an 'Initial' page at island_dock,
    which means there cannot be any move once a dock filter was set.
    Otherwise it may return untrustable results.

    By default all properties of the character are scanned.
    You can set the required properties by calling enable() or disable().
    disable() will simply skip scanning and set those properties to None.
    To keey them and ignore limitations, use set_limitation(property=None).

    Args:
        emotion (tuple): (min, max) of emotion level. Will be limited in range [0, 150].
        emotion_limit (tuple): (min, max) of emotion limit. Will be limited in range [100, 150].
        status (list): ['any', 'free', 'occupied'].
    """
    def __init__(
            self,
            grids=ISLAND_DOCK_CARD_GRIDS,
            identity: str = 'any',
            emotion: Tuple[int, int] = (0, 999),
            emotion_limit: Tuple[int, int] = (100, 999),
            grade: str = 'any',
            status: str = 'any'
    ) -> None:
        super().__init__()
        self._results = []
        self.grids = grids
        self.limitation: Dict[str, Union[None, Tuple[int, int], List[str], str]] = {
            'identity': 'any',
            'emotion': (0, 999),
            'emotion_limit': (100, 999),
            'grade': 'any',
            'status': 'any'
        }

        self.sub_scanners: Dict[str, Scanner] = {
            'identity': IdentityScanner(grids),
            'emotion': EmotionScanner(grids),
            'emotion_limit': EmotionLimitScanner(grids),
            'grade': GradeScanner(grids),
            'status': StatusScanner(grids),
        }

        self.set_limitation(identity=identity, emotion=emotion, emotion_limit=emotion_limit, grade=grade, status=status)

    def _scan(self, image) -> List[Character]:
        for scanner in self.sub_scanners.values():
            scanner.scan(image, cached=True)

        candidates: List[Character] = [
            Character(
                identity=identity,
                emotion=emotion,
                emotion_limit=emotion_limit,
                grade=grade,
                status=status,
                button=button
            )
            for identity, emotion, emotion_limit, grade, status, button in zip(
                self.sub_scanners['identity'].results,
                self.sub_scanners['emotion'].results,
                self.sub_scanners['emotion_limit'].results,
                self.sub_scanners['grade'].results,
                self.sub_scanners['status'].results,
                self.grids.buttons
            )
        ]

        for scanner in self.sub_scanners.values():
            scanner.clear()

        return candidates

    def scan(self, image, cached=False, output=True) -> Union[List[Character], None]:
        candidates = super().scan(image, cached=cached, output=output)
        if not cached:
            return [candidate for candidate in candidates
                    if candidate.satisfy_limitation(self.limitation)]

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
            ['emotion', 'emotion_limit', 'grade', 'status']
        """
        for name, scanner in self.sub_scanners.items():
            if name in args:
                scanner.enable()

    def disable(self, *args) -> None:
        """
        Disable property sub-scanners.

        Supported properties includes:
            ['emotion', 'emotion_limit', 'status']
        """
        for name, scanner in self.sub_scanners.items():
            if name in args:
                scanner.disable()

    def set_limitation(self, **kwargs) -> None:
        """
        Args:
            emotion (tuple): (min, max) of emotion level. Will be limited in range [0, 999].
            emotion_limit (tuple): (min, max) of emotion limit. Will be limited in range [100, 999].
            grade (str): ['any', 'S', 'A', 'B', 'C', 'D', 'E']
            status (str): ['any', 'free', 'occupied']
        """
        for attr in self.limitation.keys():
            value = kwargs.get(attr, self.limitation[attr])
            self.limit_value(attr, value)

        logger.info(f'Limitations set to {self.limitation}')
