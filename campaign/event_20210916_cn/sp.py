from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_base import CampaignBase

MAP = CampaignMap('SP')
MAP.shape = 'H8'
MAP.camera_data = ['C4', 'C5']
MAP.camera_data_spawn_point = ['C5']
MAP.map_data = """
    ++ ++ ++ -- -- ++ ++ ++
    ++ ++ -- -- ++ -- ++ ++
    ++ -- -- ++ -- MB -- ++
    -- -- ME -- -- -- ++ --
    -- -- -- ME -- ++ -- --
    -- SP __ -- ME -- -- ++
    ++ -- SP -- -- -- ++ ++
    ++ ++ -- -- -- ++ ++ ++
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
"""
MAP.fortress_data = [('D4', 'D6', 'C5', 'E5'), 'E4']
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1},
    {'battle': 2},
    {'battle': 3},
    {'battle': 4},
    {'battle': 5},
    {'battle': 6},
    {'battle': 7, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
A7, B7, C7, D7, E7, F7, G7, H7, \
A8, B8, C8, D8, E8, F8, G8, H8, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    # MAP_SIREN_TEMPLATE = ['1564301', '1564302', '1564303']
    # MOVABLE_ENEMY_TURN = (2,)
    # MAP_HAS_SIREN = True
    # MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    # ===== End of generated config =====

    MAP_IS_ONE_TIME_STAGE = True
    MAP_HAS_FORTRESS = True
    MAP_SWIPE_PREDICT = False
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 40),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 24, 255),
        'prominence': 10,
        'distance': 50,
        # 'width': (0, 7),
        'wlen': 1000
    }
    HOMO_CANNY_THRESHOLD = (60, 60)
    # MAP_ENEMY_GENRE_DETECTION_SCALING = {
    #     'DD': 1.111,
    #     'CL': (1, 1.111),
    #     'CA': (1, 1.111),
    #     'CV': 1.111,
    #     'BB': 1.111,
    # }
    MAP_SWIPE_MULTIPLY = 1.527
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.476


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True

        return self.battle_default()

    def battle_7(self):
        return self.fleet_boss.clear_boss()
