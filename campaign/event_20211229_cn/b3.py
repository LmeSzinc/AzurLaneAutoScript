from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .b1 import Config as ConfigBase
from .campaign_base import CampaignBase

MAP = CampaignMap('B3')
MAP.shape = 'L6'
MAP.camera_data = ['E3', 'G4', 'I3']
MAP.camera_data_spawn_point = ['D4']
MAP.map_data = """
    ++ ++ -- -- -- ME ME -- -- -- ++ ++
    ++ -- ++ ++ Me -- -- MS ++ ++ ++ ++
    -- Me Me ++ -- ME ++ -- ++ -- -- MB
    -- -- __ -- MS -- ++ -- -- MS -- MB
    SP -- -- Me ++ ++ ME -- ME -- ++ ++
    -- SP -- ++ ++ ++ -- ME -- ME ++ ++
"""
MAP.map_data_loop = """
    ++ ++ -- -- Me ME ME Me -- -- ++ ++
    ++ -- ++ ++ -- -- -- -- ++ ++ ++ ++
    -- MS Me ++ -- MS ++ -- ++ ME -- MB
    -- -- __ -- -- MS ++ -- -- -- -- MB
    SP -- -- Me ++ ++ ME -- ME -- ++ ++
    -- SP -- ++ ++ ++ -- ME -- ME ++ ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 3},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5, 'boss': 1},
]
MAP.spawn_data_loop = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5, 'enemy': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, L1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, L2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, L3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, L4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, L5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, L6, \
    = MAP.flatten()


class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====

    MAP_SIREN_TEMPLATE = ['Lover']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_SWIPE_MULTIPLY = (1.123, 1.144)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.086, 1.106)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.054, 1.073)


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    MAP_ENEMY_SEARCHING_OVERLAY_TRANSPARENCY_THRESHOLD = 0.65

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_5(self):
        return self.fleet_boss.clear_boss()
