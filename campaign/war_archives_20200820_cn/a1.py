from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from ..campaign_war_archives.campaign_base import CampaignBase

MAP = CampaignMap('A1')
MAP.shape = 'H6'
MAP.camera_data = ['D2', 'D4', 'E2', 'E4']
MAP.camera_data_spawn_point = ['D4']
MAP.map_data = """
    -- ++ -- ME -- -- ME --
    Me ++ -- MB -- Me ++ --
    -- -- __ ++ ++ -- -- ME
    -- Me -- ++ ++ -- -- ME
    SP -- ME ME -- MS -- --
    SP SP -- -- -- ME MB --
"""
MAP.weight_data = """
    10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1, 'boss': 1},
    {'battle': 4, 'enemy': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
    = MAP.flatten()


class Config:
    MAP_SIREN_TEMPLATE = ['Arethusa']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True

    MAP_HAS_AMBUSH = False
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_SWIPE_MULTIPLY = 1.764


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True

        return self.battle_default()

    def battle_3(self):
        return self.fleet_1.clear_boss()
