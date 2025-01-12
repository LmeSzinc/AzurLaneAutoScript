from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_base import CampaignBase
from .d1 import Config as ConfigBase

MAP = CampaignMap('D2')
MAP.shape = 'J8'
MAP.camera_data = ['D2', 'D6', 'G2', 'G6']
MAP.camera_data_spawn_point = ['G2']
MAP.map_data = """
    -- ME ++ ++ ++ -- Me ++ SP --
    ++ -- Me ++ ME -- -- -- -- SP
    ++ ME -- MS -- MS -- ME -- --
    ME -- ++ -- __ -- ++ ++ -- --
    -- -- -- ME -- Me ++ ++ -- ME
    ++ ++ ME -- -- MS -- -- MS --
    ++ MB -- -- ++ ME -- -- -- ++
    ++ ++ ME -- -- -- -- Me ++ ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
"""
MAP.fortress_data = ['I7', 'C7']
MAP.spawn_data = [
    {'battle': 0, 'enemy': 1, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2, 'siren': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5, 'enemy': 1},
    {'battle': 6, 'boss': 1},
]
MAP.spawn_data_loop = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2, 'siren': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5, 'enemy': 1},
    {'battle': 6, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, J8, \
    = MAP.flatten()


class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['CL', 'CA', 'BB']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====

    MAP_HAS_FORTRESS = True
    MAP_SWIPE_MULTIPLY = (1.174, 1.196)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.135, 1.156)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.102, 1.122)


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True

        return self.battle_default()

    def battle_6(self):
        return self.fleet_boss.clear_boss()
