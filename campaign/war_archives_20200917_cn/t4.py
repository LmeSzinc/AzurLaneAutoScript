from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_base import CampaignBase
from .t1 import Config as ConfigBase

MAP = CampaignMap('T4')
MAP.shape = 'K9'
MAP.camera_data = ['D2', 'D5', 'D7', 'H2', 'H5', 'H7']
MAP.camera_data_spawn_point = ['D2', 'D7']
MAP.portal_data = [('I5', 'C5'), ('C5', 'I5'), ('E5', 'E3'), ('E3', 'E5'), ('G5', 'G7'), ('G7', 'G5')]
MAP.map_data = """
    Me -- -- ++ Me -- ME -- ME ++ ++
    -- MS -- ++ -- SP -- __ -- MS --
    -- -- Me ++ -- -- -- ME -- -- --
    ME -- ++ ++ ++ ++ ++ ++ ++ -- ME
    -- -- -- ++ -- MB -- ++ -- -- --
    ME -- ++ ++ ++ ++ ++ ++ ++ -- ME
    -- -- -- ME -- -- -- ++ Me -- --
    -- MS -- __ -- SP -- ++ -- MS --
    ++ ++ ME -- ME -- Me ++ -- -- Me
"""
MAP.map_data_loop = """
    Me -- -- ++ Me -- ME -- ME ++ ++
    -- MS -- -- -- SP -- __ -- MS --
    -- -- Me ++ -- -- -- ME -- -- --
    ME -- ++ ++ -- ++ -- ++ ++ -- ME
    -- -- -- ++ -- MB -- ++ -- -- --
    ME -- ++ ++ -- ++ -- ++ ++ -- ME
    -- -- -- ME -- -- -- ++ Me -- --
    -- MS -- __ -- SP -- -- -- MS --
    ++ ++ ME -- ME -- Me ++ -- -- Me
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 10 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2, 'boss': 1},
    {'battle': 5, 'enemy': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, K7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, J8, K8, \
A9, B9, C9, D9, E9, F9, G9, H9, I9, J9, K9, \
    = MAP.flatten()


class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['CL', 'SS']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_PORTAL = True
    # ===== End of generated config =====

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 33),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 33, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }
    HOMO_EDGE_COLOR_RANGE = (0, 33)
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.82
    MAP_SWIPE_MULTIPLY = 1.88


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.config.MAP_HAS_MOVABLE_ENEMY:
            self.fleet_2_push_forward()

        if self.clear_siren():
            return True

        return self.battle_default()

    def battle_4(self):
        return self.clear_boss()
