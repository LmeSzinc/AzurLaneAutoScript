import re
from dataclasses import dataclass
from functools import cached_property
from typing import ClassVar

from module.exception import ScriptError
import module.config.server as server

REGEX_PUNCTUATION = re.compile(r'[,.\'"，。\-—/\\\n\t]')


def parse_name(n):
    n = REGEX_PUNCTUATION.sub('', str(n)).lower()
    return n


@dataclass
class Keyword:
    id: int
    cn: str
    en: str
    jp: str
    tw: str

    """
    Instance attributes and methods
    """

    @cached_property
    def cn_parsed(self) -> str:
        return parse_name(self.cn)

    @cached_property
    def en_parsed(self) -> str:
        return parse_name(self.en)

    @cached_property
    def jp_parsed(self) -> str:
        return parse_name(self.jp)

    @cached_property
    def tw_parsed(self) -> str:
        return parse_name(self.tw)

    def _keywords_to_find(self, in_current_server=False, ignore_punctuation=True):
        if in_current_server:
            match server.server:
                case 'cn':
                    if ignore_punctuation:
                        return [self.cn_parsed]
                    else:
                        return [self.cn]
                case 'en':
                    if ignore_punctuation:
                        return [self.en_parsed]
                    else:
                        return [self.en]
                case 'jp':
                    if ignore_punctuation:
                        return [self.jp_parsed]
                    else:
                        return [self.jp]
                case 'tw':
                    if ignore_punctuation:
                        return [self.tw_parsed]
                    else:
                        return [self.tw]
        else:
            if ignore_punctuation:
                return [
                    self.cn_parsed,
                    self.en_parsed,
                    self.jp_parsed,
                    self.tw_parsed,
                ]
            else:
                return [
                    self.cn,
                    self.en,
                    self.jp,
                    self.tw,
                ]

    """
    Class attributes and methods
    """

    instances: ClassVar = {}

    def __post_init__(self):
        self.__class__.instances[self.id] = self

    @classmethod
    def find(cls, name, in_current_server=False, ignore_punctuation=True):
        """
        Args:
            name: Name in any server or instance id.
            in_current_server: True to search the names from current server only.
            ignore_punctuation: True to remove punctuations and turn into lowercase before searching.

        Returns:
            Keyword instance.

        Raises:
            ScriptError: If nothing found.
        """
        # Already a keyword
        if isinstance(name, Keyword):
            return name
        # Probably an ID
        if isinstance(name, int) or (isinstance(name, str) and name.isdigit()):
            try:
                return cls.instances[int(name)]
            except KeyError:
                pass

        name = parse_name(name)
        instance: Keyword
        for instance in cls.instances.values():
            for keyword in instance._keywords_to_find(
                    in_current_server=in_current_server, ignore_punctuation=ignore_punctuation):
                if name == keyword:
                    return instance

        raise ScriptError(f'Cannot find a {cls.__name__} instance that matches "{name}"')


@dataclass
class Zone(Keyword):
    shape: str
    hazard_level: int
    region: int


DIC = {
    0: {'shape': 'J10', 'hazard_level': 1, 'cn': 'NY', 'en': 'NY City', 'jp': 'NYシティ', 'tw': '紐約',
        'area_pos': (262, 567), 'offset_pos': (15, 15), 'region': 3},
    1: {'shape': 'J10', 'hazard_level': 1, 'cn': '利维浦', 'en': 'Liverpool', 'jp': 'リバープール', 'tw': '利物浦',
        'area_pos': (1446, 887), 'offset_pos': (15, 15), 'region': 2},
    2: {'shape': 'J10', 'hazard_level': 1, 'cn': '直布罗特', 'en': 'Gibraltar', 'jp': 'ジブラルタル', 'tw': '直布羅陀',
        'area_pos': (1418, 495), 'offset_pos': (15, 15), 'region': 4},
    3: {'shape': 'J10', 'hazard_level': 1, 'cn': '圣彼得伯格', 'en': 'St. Petersburg', 'jp': 'ペテルブルク', 'tw': '聖彼得堡',
        'area_pos': (1998, 1095), 'offset_pos': (15, 15), 'region': 2},
}
Zone(id=0, cn='NY', en='NY City', jp='NYシティ', tw='紐約', shape='J10', hazard_level=1, region=3)
Zone(id=1, cn='利维浦', en='Liverpool', jp='リバープール', tw='利物浦', shape='J10', hazard_level=1, region=2)
Zone(id=2, cn='直布罗特', en='Gibraltar', jp='ジブラルタル', tw='直布羅陀', shape='J10', hazard_level=1, region=3)

print(Zone.find('直布羅陀'))
