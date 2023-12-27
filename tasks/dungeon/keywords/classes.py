from dataclasses import dataclass
from functools import cached_property
from typing import ClassVar

from module.exception import ScriptError
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

    @cached_property
    def is_Calyx_Golden(self):
        return 'Calyx_Golden' in self.name

    @cached_property
    def is_Calyx_Crimson(self):
        return 'Calyx_Crimson' in self.name

    @cached_property
    def is_Calyx(self):
        return self.is_Calyx_Golden or self.is_Calyx_Crimson

    @cached_property
    def is_Stagnant_Shadow(self):
        return 'Stagnant_Shadow' in self.name

    @cached_property
    def is_Cavern_of_Corrosion(self):
        return 'Cavern_of_Corrosion' in self.name

    @cached_property
    def is_Echo_of_War(self):
        return 'Echo_of_War' in self.name

    @cached_property
    def is_Simulated_Universe(self):
        return 'Simulated_Universe' in self.name

    @cached_property
    def is_Forgotten_Hall(self):
        for word in [
            'Forgotten_Hall',
            'Memory_of_Chaos',
            'Last_Vestiges',
            'Navis_Astriger',
        ]:
            if word in self.name:
                return True
        return False

    @cached_property
    def is_Pure_Fiction(self):
        for word in [
            'Pure_Fiction',
        ]:
            if word in self.name:
                return True
        return False

    @cached_property
    def is_daily_dungeon(self):
        return self.is_Calyx_Golden or self.is_Calyx_Crimson or self.is_Stagnant_Shadow or self.is_Cavern_of_Corrosion

    @cached_property
    def is_weekly_dungeon(self):
        return self.is_Echo_of_War

    @cached_property
    def dungeon_nav(self) -> DungeonNav:
        import tasks.dungeon.keywords.nav as KEYWORDS_DUNGEON_NAV
        if self.is_Simulated_Universe:
            return KEYWORDS_DUNGEON_NAV.Simulated_Universe
        if self.is_Calyx_Golden:
            return KEYWORDS_DUNGEON_NAV.Calyx_Golden
        if self.is_Calyx_Crimson:
            return KEYWORDS_DUNGEON_NAV.Calyx_Crimson
        if self.is_Stagnant_Shadow:
            return KEYWORDS_DUNGEON_NAV.Stagnant_Shadow
        if self.is_Cavern_of_Corrosion:
            return KEYWORDS_DUNGEON_NAV.Cavern_of_Corrosion
        if self.is_Echo_of_War:
            return KEYWORDS_DUNGEON_NAV.Echo_of_War
        if self.is_Forgotten_Hall:
            return KEYWORDS_DUNGEON_NAV.Forgotten_Hall
        if self.is_Pure_Fiction:
            return KEYWORDS_DUNGEON_NAV.Pure_Fiction

        raise ScriptError(f'Cannot convert {self} to DungeonNav, please check keyword extractions')

    @cached_property
    def rogue_theme(self) -> str:
        """
        Returns:
            'rogue' for normal simulated universe farmed every week
            'dlc' for special rogue theme
            '' for non-rogue
        """
        if self.is_Simulated_Universe:
            if self.name.startswith('Simulated_Universe_World'):
                return 'rogue'
            else:
                return 'dlc'
        else:
            return ''


@dataclass(repr=False)
class DungeonEntrance(Keyword):
    instances: ClassVar = {}


@dataclass(repr=False)
class DungeonDetailed(Keyword):
    instances: ClassVar = {}
