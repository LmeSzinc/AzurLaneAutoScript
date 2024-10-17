from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .a1 import Config as ConfigBase
from .campaign_base import CampaignBase

MAP = CampaignMap('A3')
MAP.shape = 'I9'
MAP.camera_data = ['E2', 'E5', 'E7', 'D5']
MAP.camera_data_spawn_point = ['F5']
MAP.map_data = """
    -- ME ME ++ ++ ++ ME ME ++
    ++ ++ -- -- -- MS -- -- ++
    ++ ++ -- Me ++ Me -- ME --
    ++ -- -- ++ -- ++ -- -- SP
    MB -- MS -- -- __ MS -- --
    ++ -- -- ++ -- ++ -- -- SP
    ++ ++ -- Me ++ Me -- ME --
    ++ ++ -- -- -- MS -- -- ++
    -- ME ME ++ ++ ++ ME ME ++
"""
MAP.weight_data = """
    50 60 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 60 50 50 50 50 50 50 50
"""
MAP.fortress_data = ['E5', 'B5']
MAP.spawn_data = [
    {'battle': 0, 'enemy': 1, 'siren': 1},
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


class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['DD']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====

    MAP_HAS_FORTRESS = True


class Campaign(CampaignBase):
    MAP = MAP
    MACHINE_FORTRESS = [E5]

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(scale=(1,)):
            return True
        if self.clear_enemy(scale=(2,), genre=['light', 'main', 'enemy']):
            return True
        if self.clear_enemy(genre=['light', 'main']):
            return True
        if self.clear_enemy(scale=[2, 3]):
            return True

        return self.battle_default()

    def battle_4(self):
        return self.clear_boss()
