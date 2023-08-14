from dataclasses import dataclass
from typing import ClassVar

from dev_tools.keyword_extract import UI_LANGUAGES
from module.ocr.keyword import Keyword


@dataclass(repr=False)
class RogueBlessing(Keyword):
    instances: ClassVar = {}
    path_id: int
    rarity: int

    @property
    def path_name(self):
        path = RoguePath.instances[self.path_id]
        return path.path_name

    @property
    def blessing_name(self):
        return [self.__getattribute__(f"{server}_parsed")
                for server in UI_LANGUAGES if hasattr(self, f"{server}_parsed")]


@dataclass(repr=False)
class RoguePath(Keyword):
    instances: ClassVar = {}

    @property
    def path_name(self):
        return [self.__getattribute__(f"{server}_parsed")
                for server in UI_LANGUAGES if hasattr(self, f"{server}_parsed")]


@dataclass(repr=False)
class RogueResonance(Keyword):
    instances: ClassVar = {}
    path_id: int
    rarity: int

    @property
    def resonance_name(self):
        return [self.__getattribute__(f"{server}_parsed")
                for server in UI_LANGUAGES if hasattr(self, f"{server}_parsed")]


@dataclass(repr=False)
class RogueCurio(Keyword):
    instances: ClassVar = {}

    @property
    def curio_name(self):
        return [self.__getattribute__(f"{server}_parsed")
                for server in UI_LANGUAGES if hasattr(self, f"{server}_parsed")]


@dataclass(repr=False)
class RogueBonus(Keyword):
    instances: ClassVar = {}
