from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .c1 import Config as ConfigBase
from .campaign_base import CampaignBase

MAP = CampaignMap('C3')
MAP.shape = 'I9'
MAP.camera_data = ['E3', 'E5', 'E7']
MAP.camera_data_spawn_point = ['E7']
MAP.map_data = """
    ++ ++ ++ -- MB -- ++ ++ ++
    ++ -- -- -- -- -- -- -- ++
    -- ME -- ME ++ ME -- ME --
    -- -- -- -- -- -- -- -- --
    -- ME -- -- -- -- -- ME --
    ++ ++ -- -- -- -- -- ++ ++
    ++ ++ Me -- Me -- Me ++ ++
    ++ Me -- -- __ -- -- Me ++
    ++ -- -- SP -- SP -- -- ++
"""
MAP.map_data_loop = """
    ++ ++ ++ -- MB -- ++ ++ ++
    ++ -- -- -- -- -- -- -- ++
    -- ME -- ME ++ ME -- ME --
    -- -- -- -- -- -- -- -- --
    -- ME -- ME -- ME -- ME --
    ++ ++ -- MS -- MS -- ++ ++
    ++ ++ Me -- Me -- Me ++ ++
    ++ Me -- -- __ -- -- Me ++
    ++ -- -- SP -- SP -- -- ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 1},
    {'battle': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'boss': 1},
]
MAP.spawn_data_loop = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, \
A9, B9, C9, D9, E9, F9, G9, H9, I9, \
    = MAP.flatten()

MAP.bouncing_enemy_data = [(C4, D4, E4, F4, G4), (C2, D2, E2, F2, G2)]
MAP.fortress_data = [(D6, F6), (C5, D5, E5, F5, G5, C6, E6, G6)]


class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====

    MAP_SWIPE_MULTIPLY = (0.993, 1.012)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (0.961, 0.978)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (0.933, 0.949)


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        if self.clear_bouncing_enemy():
            return True
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_5(self):
        return self.fleet_boss.clear_boss()
