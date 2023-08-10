from dataclasses import dataclass
from typing import ClassVar

from module.ocr.keyword import Keyword


@dataclass(repr=False)
class RogueBlessing(Keyword):
    instances: ClassVar = {}
    path_id: int
    rarity: int


@dataclass(repr=False)
class RoguePath(Keyword):
    instances: ClassVar = {}


@dataclass(repr=False)
class RogueResonance(Keyword):
    instances: ClassVar = {}
    path_id: int
    rarity: int
