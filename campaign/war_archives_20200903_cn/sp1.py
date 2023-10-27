from .campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('SP1')
MAP.shape = 'K7'
MAP.camera_data = ['D3', 'D5', 'H3', 'H5']
MAP.camera_data_spawn_point = ['D2']
MAP.map_data = """
    ++ ++ ++ -- MS -- -- -- ME ++ --
    -- ME -- ++ -- ++ ++ -- ME ++ MB
    SP -- ME -- -- ME ++ -- Me ++ Me
    SP -- __ -- -- ++ ME -- ME -- --
    ME -- -- -- ME -- -- -- -- -- --
    ME -- -- ++ -- -- -- -- -- -- --
    -- -- -- ++ -- -- -- ++ ++ ++ ++
"""
MAP.map_data_loop = """
    ++ ++ ++ -- MS -- -- -- ME ++ --
    -- ME -- -- -- ++ ++ -- ME ++ MB
    SP -- ME -- -- ME ++ -- Me -- Me
    SP -- __ -- -- -- ME -- ME -- --
    ME -- -- -- ME -- -- -- -- -- --
    ME -- -- ++ -- -- -- -- -- -- --
    -- -- -- ++ -- -- -- -- ++ ++ ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 55 50 50 50 50 30
    50 50 50 50 50 50 50 50 50 50 40
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
"""
MAP.land_based_data = [['H7', 'up'], ['F4', 'down'], ['J3', 'down'], ['D2', 'down']]
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, K7, \
    = MAP.flatten()

road_main = RoadGrids([K3])


class Config:
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
        if self.clear_siren():
            return True

        self.clear_mechanism()

        if self.clear_roadblocks([road_main]):
            return True

        return self.battle_default()

    def battle_4(self):
        return self.clear_boss()
