from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from ..campaign_war_archives.campaign_base import CampaignBase
from .b1 import Config as ConfigBase

MAP = CampaignMap('B2')
MAP.shape = 'I7'
MAP.camera_data = ['D2', 'D5', 'F2', 'F5']
MAP.camera_data_spawn_point = ['D5']
MAP.map_data = """
    ++ -- ME ME ME ME -- -- ++
    MB Me ME ME ++ -- ME -- ++
    MB MB ++ ++ ++ ++ ++ ME --
    ++ ++ ++ ++ -- -- ME Me --
    SP SP -- ++ -- ME Me -- ++
    SP -- -- Me -- -- ++ -- --
    SP SP ++ -- -- -- ++ -- MM
"""
MAP.weight_data = """
    50 10 20 20 10 20 50 50 50
    20 20 30 30 50 50 50 50 50
    10 10 50 50 50 50 50 10 50
    50 50 50 50 50 10 20 10 50
    50 50 50 50 10 30 30 50 50
    50 50 50 20 50 40 50 50 50
    50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 4},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1, 'mystery': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5},
    {'battle': 6, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, \
    = MAP.flatten()

ROAD_MAIN = RoadGrids([D6, [G4, G5], H4, H3, F1, D1, C1, B2])

class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = True
    MAP_HAS_MYSTERY = True
    # ===== End of generated config =====


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        self.fleet_2_push_forward()
        if self.clear_roadblocks([ROAD_MAIN], strongest=True):
            return True

        if self.clear_potential_roadblocks([ROAD_MAIN], strongest=True):
            return True

        return self.battle_default()

    def battle_3(self):
        self.clear_all_mystery()

        return self.battle_0()

    def battle_6(self):
        return self.fleet_boss.clear_boss()
