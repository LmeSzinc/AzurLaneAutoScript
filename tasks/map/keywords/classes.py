from dataclasses import dataclass
from functools import cached_property
from typing import ClassVar

from module.exception import ScriptError
from module.ocr.keyword import Keyword


@dataclass(repr=False)
class MapPlane(Keyword):
    instances: ClassVar = {}

    # 0, 1, 2, 3
    world_id: int
    # 1010201
    plane_id: int

    # Map floors, 'F1' by default
    # Example: ['B1', 'F1', 'F2']
    floors = ['F1']

    # Page on bigmap sidebar
    # 'top' or 'bottom'
    page = 'top'

    @classmethod
    def find_plane_id(cls, plane_id):
        """
        Args:
            plane_id:

        Returns:
            MapPlane: MapPlane object or None
        """
        for instance in cls.instances.values():
            if instance.plane_id == plane_id:
                return instance
        return None

    def __hash__(self) -> int:
        return super().__hash__()

    @cached_property
    def world(self) -> "MapWorld":
        """
        Returns:
            MapWorld: MapWorld object or None
        """
        return MapWorld.find_world_id(self.world_id)

    @cached_property
    def has_multiple_floors(self):
        return self.floors and self.floors != ['F1']

    def convert_to_floor_index(self, floor: str | int) -> int:
        """
        Args:
            floor: int for floor index counted from bottom, such as 1, 2, 3
                str for floor names in game, such as "B1", "F1", "F2"

        Returns:
            int: 1 to 3 counted from bottom.

        Raises:
            ScriptError: If floor doesn't exist
        """
        if isinstance(floor, int):
            # Check exist
            try:
                _ = self.floors[floor - 1]
                return floor
            except (IndexError, ValueError):
                raise ScriptError(f'Plane {self} does not have floor index {floor}')
        elif isinstance(floor, str):
            # Convert to floor index
            floor = floor.upper()
            try:
                return self.floors.index(floor) + 1
            except (IndexError, ValueError):
                raise ScriptError(f'Plane {self} does not have floor name {floor}')
        else:
            raise ScriptError(f'Plane {self} does not have floor {floor}')

    def convert_to_floor_name(self, floor: str | int) -> str:
        """
        Args:
            floor: int for floor index counted from bottom, such as 1, 2, 3
                str for floor names in game, such as "B1", "F1", "F2"

        Returns:
            str: Floor names in game, such as "B1", "F1", "F2"

        Raises:
            ScriptError: If floor doesn't exist
        """
        if isinstance(floor, int):
            # Convert to floor index
            try:
                return self.floors[floor - 1]
            except (IndexError, ValueError):
                raise ScriptError(f'Plane {self} does not have floor index {floor}')
        elif isinstance(floor, str):
            # Check exist
            floor = floor.upper()
            try:
                _ = self.floors.index(floor) + 1
                return floor
            except (IndexError, ValueError):
                raise ScriptError(f'Plane {self} does not have floor name {floor}')
        else:
            raise ScriptError(f'Plane {self} does not have floor {floor}')

    @cached_property
    def rogue_domain(self) -> str:
        if self.name.startswith('Rogue_Domain'):
            return self.name.removeprefix('Rogue_Domain')
        else:
            return ''

    @cached_property
    def is_rogue_combat(self) -> bool:
        return self.rogue_domain in ['Combat']

    @cached_property
    def is_rogue_occurrence(self) -> bool:
        return self.rogue_domain in ['Occurrence', 'Encounter', 'Transaction']

    @cached_property
    def is_rogue_respite(self) -> bool:
        return self.rogue_domain in ['Respite']

    @cached_property
    def is_rogue_elite(self) -> bool:
        return self.rogue_domain in ['Elite', 'Boss']


@dataclass(repr=False)
class MapWorld(Keyword):
    instances: ClassVar = {}

    # 0, 1, 2, 3
    world_id: int
    # Herta
    short_name: str

    @classmethod
    def find_world_id(cls, world_id):
        """
        Args:
            world_id:

        Returns:
            MapWorld: MapWorld object or None
        """
        for instance in cls.instances.values():
            if instance.world_id == world_id:
                return instance
        return None

    def __hash__(self) -> int:
        return super().__hash__()

    @cached_property
    def is_Herta(self):
        return self.short_name == 'Herta'

    @cached_property
    def is_Jarilo(self):
        return self.short_name == 'Jarilo'

    @cached_property
    def is_Luofu(self):
        return self.short_name == 'Luofu'

    @cached_property
    def is_Penacony(self):
        return self.short_name == 'Penacony'
