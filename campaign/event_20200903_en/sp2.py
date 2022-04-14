from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .sp1 import Config as ConfigBase

MAP = CampaignMap('SP2')
MAP.shape = 'K7'
MAP.camera_data = ['D3', 'D5', 'H3', 'H5']
MAP.camera_data_spawn_point = ['D2', 'D5']
MAP.map_data = """
    ++ ++ ++ -- -- -- -- ME ++ ++ --
    ME -- ++ -- -- ++ -- -- MS ++ --
    SP -- -- MS -- ++ -- -- -- Me --
    -- ME -- ME ++ ++ ME __ -- -- ++
    SP -- -- ME ++ ++ ME -- ME Me --
    ME ++ ++ -- -- -- -- -- ++ ME MB
    -- ++ -- ME ME -- -- ME ++ ++ ++
"""
MAP.map_data_loop = """
    ++ ++ ++ -- -- -- -- ME ++ ++ --
    ME -- -- -- -- ++ -- -- MS ++ --
    SP -- -- MS -- -- -- -- -- Me --
    -- ME -- ME ++ ++ ME __ -- -- ++
    SP -- -- ME ++ ++ ME -- ME Me --
    ME ++ -- -- -- -- -- -- -- ME MB
    -- ++ -- ME ME -- -- ME ++ ++ ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 40 30
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
"""
MAP.land_based_data = [['I6', 'up'], ['C6', 'right'], ['F3', 'right'], ['C2', 'down']]
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 2},
    # {'battle': 2, 'enemy': 1, 'mystery': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4},
    {'battle': 5, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, K7, \
    = MAP.flatten()

road_main = RoadGrids([J5])


class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['Z18']
    MOVABLE_ENEMY_TURN = (3,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_LAND_BASED = True
    # ===== End of generated config =====


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if not self.config.MAP_HAS_MOVABLE_ENEMY:
            self.fleet_2_push_forward()

        if self.clear_siren():
            return True

        self.clear_mechanism()

        if self.config.MAP_HAS_MOVABLE_ENEMY:
            self.fleet_2_push_forward()

        if self.clear_roadblocks([road_main]):
            return True

        return self.battle_default()

    def battle_5(self):
        return self.fleet_boss.clear_boss()
