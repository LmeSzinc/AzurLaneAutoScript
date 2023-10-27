from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from ..campaign_war_archives.campaign_base import CampaignBase
from .b1 import Config as ConfigBase

MAP = CampaignMap('B3')
MAP.shape = 'F10'
MAP.camera_data = ['C2', 'C6', 'C8']
MAP.camera_data_spawn_point = ['C8']
MAP.map_data = """
    ++ ++ ++ ++ ++ ++
    ++ MB ++ ++ MB ++
    ++ -- ++ ++ -- ++
    ++ ME ME ME ME ++
    ++ ME ME ME ME ++
    -- Me ME ME Me --
    ME ++ ++ ++ ++ Me
    Me ME -- -- ME Me
    -- -- SP SP -- --
    ++ ++ ++ ++ ++ ++
"""
MAP.weight_data = """
    50 50 50 50 50 50
    50 10 50 50 10 50
    50 10 50 50 10 50
    50 10 40 40 10 50
    50 20 40 40 20 50
    50 30 20 20 30 50
    20 50 50 50 50 20
    20 20 50 50 20 20
    50 50 50 50 50 50
    50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 4},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'enemy': 1},
    {'battle': 6},
    {'battle': 7, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, \
A2, B2, C2, D2, E2, F2, \
A3, B3, C3, D3, E3, F3, \
A4, B4, C4, D4, E4, F4, \
A5, B5, C5, D5, E5, F5, \
A6, B6, C6, D6, E6, F6, \
A7, B7, C7, D7, E7, F7, \
A8, B8, C8, D8, E8, F8, \
A9, B9, C9, D9, E9, F9, \
A10, B10, C10, D10, E10, F10, \
    = MAP.flatten()


class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = True
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=2):
            return True

        return self.battle_default()

    def battle_5(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_7(self):
        return self.fleet_boss.clear_boss()
