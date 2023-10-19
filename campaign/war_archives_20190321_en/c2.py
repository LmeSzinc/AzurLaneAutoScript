from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from ..campaign_war_archives.campaign_base import CampaignBase
from .c1 import Config as ConfigBase

MAP = CampaignMap('C2')
MAP.shape = 'H6'
MAP.camera_data = ['D2', 'D4', 'E2', 'E4']
MAP.camera_data_spawn_point = ['D4']
MAP.map_data = """
    -- -- ++ ++ ++ ++ -- MM
    Me -- Me -- ME -- Me --
    -- ++ -- ++ ++ ME ++ ME
    -- -- ME ++ ++ Me ++ --
    -- -- ++ MB ME Me -- --
    SP SP ++ MB ME ME Me --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50
    80 50 50 35 50 25 50 20
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 10 50 15 50
    50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 4},
    {'battle': 1, 'enemy': 2, 'mystery': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5},
    {'battle': 6, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
    = MAP.flatten()

ROAD_MAIN = RoadGrids([[A2, C4], C2, E2, G2, H3, F5, E5])

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

    def battle_6(self):
        self.clear_all_mystery()
        return self.fleet_boss.clear_boss()
