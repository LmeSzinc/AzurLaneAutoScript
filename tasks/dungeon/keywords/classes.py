from dataclasses import dataclass
from typing import ClassVar

from module.ocr.keyword import Keyword


@dataclass
class DungeonNav(Keyword):
    instances: ClassVar = {}
    pass


@dataclass
class DungeonTab(Keyword):
    instances: ClassVar = {}
    pass
