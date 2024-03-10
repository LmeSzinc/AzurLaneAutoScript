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

    plane_id: int

    @cached_property
    def plane(self):
        """
        Returns:
            MapPlane: MapPlane object or None
        """
        from tasks.map.keywords import MapPlane
        return MapPlane.find_plane_id(self.plane_id)

    @cached_property
    def world(self):
        """
        Returns:
            MapWorld: MapWorld object or None
        """
        if self.plane is not None:
            return self.plane.world
        else:
            return None

    @cached_property
    def is_Calyx_Golden(self):
        return 'Calyx_Golden' in self.name

    @cached_property
    def is_Calyx_Golden_Memories(self):
        return 'Calyx_Golden_Memories' in self.name

    @cached_property
    def is_Calyx_Golden_Aether(self):
        return 'Calyx_Golden_Aether' in self.name

    @cached_property
    def is_Calyx_Golden_Treasures(self):
        return 'Calyx_Golden_Treasures' in self.name

    @cached_property
    def is_Calyx_Crimson(self):
        return 'Calyx_Crimson' in self.name

    @cached_property
    def Calyx_Crimson_Path(self):
        """
        Returns:
            RoguePath: RoguePath object or None
        """
        if not self.is_Calyx_Crimson:
            return None
        from tasks.rogue.keywords import RoguePath
        for path in RoguePath.instances.values():
            if path.name in self.name:
                return path
            elif path.name == 'The_Harmony' and 'Harmony' in self.name:
                return path
        return None

    @cached_property
    def is_Calyx(self):
        return self.is_Calyx_Golden or self.is_Calyx_Crimson

    @cached_property
    def is_Stagnant_Shadow(self):
        return 'Stagnant_Shadow' in self.name

    @cached_property
    def Stagnant_Shadow_Combat_Type(self):
        """
        Returns:
            CombatType: CombatType object or None
        """
        if not self.is_Stagnant_Shadow:
            return None
        from tasks.dungeon.keywords import DungeonDetailed
        detail = DungeonDetailed.find_name(self.name)
        if detail is None:
            return None
        from tasks.character.keywords import CombatType
        for type_ in CombatType.instances.values():
            if type_.cn in detail.cn[:10]:
                return type_
        return None

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
