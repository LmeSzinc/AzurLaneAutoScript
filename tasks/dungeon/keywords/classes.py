from dataclasses import dataclass
from typing import ClassVar

from module.ocr.keyword import Keyword


@dataclass(repr=False)
class DungeonNav(Keyword):
    instances: ClassVar = {}


@dataclass(repr=False)
class DungeonTab(Keyword):
    instances: ClassVar = {}


@dataclass(repr=False)
class DungeonList(Keyword):
    instances: ClassVar = {}

    @property
    def is_Calyx_Golden(self):
        return 'Calyx_Golden' in self.name

    @property
    def is_Calyx_Crimson(self):
        return 'Calyx_Crimson' in self.name

    @property
    def is_Stagnant_Shadow(self):
        return 'Stagnant_Shadow' in self.name

    @property
    def is_Cavern_of_Corrosion(self):
        return 'Cavern_of_Corrosion' in self.name

    @property
    def is_Echo_of_War(self):
        return 'Echo_of_War' in self.name

    @property
    def is_Simulated_Universe(self):
        return 'Simulated_Universe' in self.name


@dataclass(repr=False)
class DungeonEntrance(Keyword):
    instances: ClassVar = {}
