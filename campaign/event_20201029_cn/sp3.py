from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_base import CampaignBase
from .sp1 import Config as ConfigBase

MAP = CampaignMap('SP3')
MAP.shape = 'I7'
MAP.camera_data = ['C2', 'C5', 'F2', 'F5']
MAP.camera_data_spawn_point = ['D2', 'D5']
MAP.camera_sight = (-2, -1, 3, 2)
MAP.map_covered = ['E3']
MAP.map_data = """
    ++ ++ ++ -- -- -- ME ++ ++
    SP -- -- -- Me -- -- ME ++
    -- -- -- MS -- MS -- -- ME
    SP -- Me -- ++ -- Me __ MB
    -- -- -- MS -- MS -- -- ME
    ME ME ++ -- ME -- -- ME ++
    -- -- ++ -- MB -- ME ++ ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3, 'siren': 2},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4},
    {'battle': 5, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, \
    = MAP.flatten()


class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['DidoIdol', 'BaltimoreIdol', 'AlbacoreIdol']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    # ===== End of generated config =====

    MAP_SWIPE_MULTIPLY = 1.847
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.786


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True

        return self.battle_default()

    def battle_5(self):
        return self.fleet_boss.clear_boss()
