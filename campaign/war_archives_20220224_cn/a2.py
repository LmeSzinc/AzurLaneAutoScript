from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .a1 import Config as ConfigBase
from ..campaign_war_archives.campaign_base import CampaignBase

MAP = CampaignMap('A2')
MAP.shape = 'H10'
MAP.camera_data = ['D2', 'E5', 'E7']
MAP.camera_data_spawn_point = ['D2']
MAP.map_data = """
    ++ -- SP SP -- -- ++ ++
    -- Me -- -- -- Me ++ ++
    Me -- -- -- -- -- Me --
    ++ ++ -- __ -- Me -- --
    -- ++ -- -- -- ++ ++ ++
    -- ME -- -- -- -- ME --
    ++ ME -- -- -- -- -- MB
    -- ME -- ME -- -- ME --
    -- ++ ME -- ME ME ++ ++
    -- -- -- -- -- -- -- ++
"""
MAP.map_data_loop = """
    ++ -- SP SP -- -- ++ ++
    -- Me -- -- -- Me ++ ++
    Me -- -- MS -- -- Me --
    ++ ++ -- __ -- Me -- --
    -- ++ -- MS -- ++ ++ ++
    -- ME -- -- ME -- ME --
    ++ ME -- -- -- -- -- MB
    -- ME -- ME -- -- ME --
    -- ++ ME -- ME ME ++ ++
    -- -- -- -- -- -- -- ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'boss': 1},
]
MAP.spawn_data_loop = [
    {'battle': 0, 'enemy': 2, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
A7, B7, C7, D7, E7, F7, G7, H7, \
A8, B8, C8, D8, E8, F8, G8, H8, \
A9, B9, C9, D9, E9, F9, G9, H9, \
A10, B10, C10, D10, E10, F10, G10, H10, \
    = MAP.flatten()

MAP.bouncing_enemy_data = [(B3, C3, D3, E3, F3), ]
MAP.fortress_data = [D5, (C5, E5, C6, D6, E6)]

class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====

    MAP_SWIPE_MULTIPLY = (1.216, 1.239)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.176, 1.198)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.142, 1.163)


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

    def battle_4(self):
        return self.clear_boss()
