from .campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger
from .a1 import Config as ConfigBase

MAP = CampaignMap('A3')
MAP.shape = 'J8'
MAP.camera_data = ['D2', 'D6', 'G2', 'G6']
MAP.camera_data_spawn_point = ['D6']
MAP.map_data = """
    ++ ++ -- ME -- -- -- ++ ++ ++
    ++ ++ MS ME -- -- -- -- ME ME
    ME -- -- __ -- MB MB -- -- --
    -- -- Me -- MS ++ ++ -- -- ME
    ++ SP -- ++ ++ ++ ME -- Me --
    ++ SP -- Me -- Me -- -- -- --
    -- ME -- -- ME -- -- MS ++ ++
    ME -- ++ ME -- ME -- -- -- ++
"""
MAP.map_data_loop = """
    ++ ++ -- ME -- -- -- ++ ++ ++
    ++ ++ MS ME -- Me -- -- ME ME
    ME -- -- __ -- MB MB -- -- --
    -- -- Me -- MS ++ ++ -- -- ME
    ++ SP -- ++ ++ ++ ME -- Me --
    ++ SP -- -- -- Me -- -- -- --
    -- ME -- -- ME -- -- MS ++ ++
    ME -- ++ ME -- ME -- -- -- ++
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
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'boss': 1},
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
    MAP_SIREN_TEMPLATE = ['CL', 'CA']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====

    MAP_HAS_DECOY_ENEMY = False
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (150, 255 - 33),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 33, 255),
        'prominence': 10,
        'distance': 50,
        # 'width': (0, 7),
        'wlen': 1000
    }
    HOMO_EDGE_COLOR_RANGE = (0, 33)
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 300
    MAP_ENEMY_GENRE_DETECTION_SCALING = {
        'DD': 1.111,
        'CL': 1.111,
        'CA': 1.111,
        'CV': 1.111,
        'BB': 1.111,
    }
    MAP_SWIPE_MULTIPLY = (0.984, 1.003)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (0.952, 0.969)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (0.924, 0.941)


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_4(self):
        return self.clear_boss()
