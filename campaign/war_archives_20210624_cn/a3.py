from ..campaign_war_archives.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .a1 import Config as ConfigBase

MAP = CampaignMap('A3')
MAP.shape = 'I6'
MAP.camera_data = ['D2', 'D4', 'F2', 'F4']
MAP.camera_data_spawn_point = ['D4', 'F4']
MAP.map_data = """
    Me -- ++ MB ++ ++ ME -- --
    -- ME ME MB ++ ++ ME ME --
    -- -- -- -- MB -- -- MS ME
    ME MS __ -- -- -- ++ ++ ++
    -- ME ++ MS -- -- -- Me MS
    -- ME ++ -- SP SP Me -- --
"""
MAP.weight_data = """
    50 50 50 50 50 50 90 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 90 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2, 'boss': 1},
    {'battle': 5, 'enemy': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, \
    = MAP.flatten()


class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['Kinu']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    # ===== End of generated config =====

    MAP_SWIPE_MULTIPLY = 1.449
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.401


class Campaign(CampaignBase):
    MAP = MAP

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
