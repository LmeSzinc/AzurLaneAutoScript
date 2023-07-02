from dataclasses import dataclass
from functools import cached_property
from typing import ClassVar

from module.ocr.keyword import Keyword


@dataclass(repr=False)
class MapPlane(Keyword):
    instances: ClassVar = {}

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
