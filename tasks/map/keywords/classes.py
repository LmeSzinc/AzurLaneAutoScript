from dataclasses import dataclass
from functools import cached_property
from typing import ClassVar

from module.exception import ScriptError
from module.ocr.keyword import Keyword


@dataclass(repr=False)
class MapPlane(Keyword):
    instances: ClassVar = {}

    # Map floors, 'F1' by default
    # Example: ['B1', 'F1', 'F2']
    floors = ['F1']

    # Page on bigmap sidebar
    # 'top' or 'bottom'
    page = 'top'

    @cached_property
    def world(self) -> str:
        """
        Returns:
            str: World name. Note that "Parlor Car" is considered as a plane of Herta.
                "Herta" for Herta Space Station
                "Jarilo" for Jarilo-VI
                "Luofu" for The Xianzhou Luofu
                "" for unknown
        """
        for world in ['Herta', 'Jarilo', 'Luofu']:
            if self.name.startswith(world):
                return world

        return ''

    @cached_property
    def is_HertaSpaceStation(self):
        return self.world == 'Herta'

    @cached_property
    def is_JariloVI(self):
        return self.world == 'Jarilo'

    @cached_property
    def is_Luofu(self):
        return self.world == 'Luofu'

    @cached_property
    def has_multiple_floors(self):
        return self.floors == ['F1']

    def convert_to_floor_index(self, floor: str) -> int:
        """
        Args:
            floor: Floor names in game, such as "B1", "F1", "F2"

        Returns:
            int: 1 to 3 counted from bottom.

        Raises:
            ScriptError: If floor doesn't exist
        """
        floor = floor.upper()
        try:
            return self.floors.index(floor) + 1
        except IndexError:
            raise ScriptError(f'Plane {self} does not have floor name {floor}')

    def convert_to_floor_name(self, floor: int) -> str:
        """
        Args:
            floor: Floor index counted from bottom, such as 1, 2, 3

        Returns:
            str: Floor names in game, such as "B1", "F1", "F2"

        Raises:
            ScriptError: If floor doesn't exist
        """
        try:
            return self.floors[floor - 1]
        except IndexError:
            raise ScriptError(f'Plane {self} does not have floor index {floor}')
