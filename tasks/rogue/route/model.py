from functools import cached_property
from typing import Any

from pydantic import BaseModel, RootModel

from tasks.map.route.model import RouteModel


class RogueWaypointModel(BaseModel):
    """
    {
        "domain": "Combat",
        "route": "Herta_StorageZone_F1_X252Y84",
        "waypoint": "spawn",
        "index": 0,
        "file": "./screenshots/rogue/Combat/Herta_StorageZone_F1_X252Y84/route/spawn.png",
        "plane": "Herta_StorageZone",
        "floor": "F1",
        "position": [
            252.8,
            84.8
        ],
        "direction": 300.1,
        "rotation": 299
    },
    """
    domain: str
    route: str
    waypoint: str
    index: int

    file: str

    plane: str
    floor: str
    position: tuple[float, float]
    direction: float
    rotation: int

    class Config:
        ignored_types = (cached_property,)

    def model_post_init(self, __context: Any) -> None:
        if self.waypoint == 'exit':
            self.waypoint = 'exit_'

    @cached_property
    def plane_floor(self):
        return f'{self.plane}_{self.floor}'

    @cached_property
    def positionXY(self):
        x, y = int(self.position[0]), int(self.position[1])
        return f'X{x}Y{y}'

    @cached_property
    def is_spawn(self) -> bool:
        return self.waypoint.startswith('spawn')

    @cached_property
    def is_exit(self) -> bool:
        return self.waypoint.startswith('exit_')

    @cached_property
    def is_exit1(self) -> bool:
        return self.waypoint.startswith('exit1')

    @cached_property
    def is_exit2(self) -> bool:
        return self.waypoint.startswith('exit2')

    @cached_property
    def is_exit_door(self) -> bool:
        return self.is_exit1 or self.is_exit2

    @cached_property
    def is_middle(self) -> bool:
        return not self.is_spawn and not self.is_exit_door and not self.is_exit_door

    @cached_property
    def is_DomainBoss(self):
        return self.domain == 'Boss'

    @cached_property
    def is_DomainCombat(self):
        return self.domain == 'Combat'

    @cached_property
    def is_DomainElite(self):
        return self.domain == 'Elite'

    @cached_property
    def is_DomainEncounter(self):
        return self.domain == 'Encounter'

    @cached_property
    def is_DomainOccurrence(self):
        return self.domain == 'Occurrence'

    @cached_property
    def is_DomainRespite(self):
        return self.domain == 'Respite'

    @cached_property
    def is_DomainTransaction(self):
        return self.domain == 'Transaction'


RogueWaypointListModel = RootModel[list[RogueWaypointModel]]


class RogueRouteModel(RouteModel):
    """
    {
        "name": "Boss_Luofu_ArtisanshipCommission_F1_X506Y495",
        "domain": "Boss",
        "route": "route.rogue.Boss.Luofu_ArtisanshipCommission_F1:Luofu_ArtisanshipCommission_F1_X506Y495",
        "plane": "Luofu_ArtisanshipCommission",
        "floor": "F1",
        "position": [
            506.0,
            495.4
        ]
    },
    """
    domain: str

    @property
    def plane_floor(self):
        return f'{self.plane}_{self.floor}'

    @property
    def is_DomainBoss(self):
        return self.domain == 'Boss'

    @property
    def is_DomainCombat(self):
        return self.domain == 'Combat'

    @property
    def is_DomainElite(self):
        return self.domain == 'Elite'

    @property
    def is_DomainEncounter(self):
        return self.domain == 'Encounter'

    @property
    def is_DomainOccurrence(self):
        return self.domain == 'Occurrence'

    @property
    def is_DomainRespite(self):
        return self.domain == 'Respite'

    @property
    def is_DomainTransaction(self):
        return self.domain == 'Transaction'


RogueRouteListModel = RootModel[list[RogueRouteModel]]
