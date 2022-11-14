from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('SP')
MAP.shape = 'M10'
MAP.camera_data = ['F6', 'I6', 'G8']
MAP.camera_data_spawn_point = ['D8']
MAP.map_data = """
    -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- ++ ++ -- -- -- -- -- --
    -- ++ ++ ++ -- -- ++ -- -- ++ ++ ++ --
    -- -- ++ ++ ++ ++ ++ ++ ++ ++ ++ -- --
    -- -- ME -- ++ ++ ++ ++ ++ -- ME -- --
    -- -- -- ME -- -- ++ -- -- ME -- -- --
    -- -- -- -- ME ++ MB ++ ME -- Me Me --
    -- SP -- -- -- MS -- MS -- -- ++ ++ --
    -- -- SP -- -- -- __ -- -- -- ++ ++ --
    -- -- -- -- -- MS -- MS -- -- -- -- --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1, 'siren': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'enemy': 1},
    {'battle': 6},
    {'battle': 7, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, L1, M1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, L2, M2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, L3, M3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, L4, M4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, L5, M5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, L6, M6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, K7, L7, M7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, J8, K8, L8, M8, \
A9, B9, C9, D9, E9, F9, G9, H9, I9, J9, K9, L9, M9, \
A10, B10, C10, D10, E10, F10, G10, H10, I10, J10, K10, L10, M10, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['Z24', 'Nuremberg', 'PeterStrasser']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    # ===== End of generated config =====

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (150, 255 - 17),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 17, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }
    HOMO_EDGE_COLOR_RANGE = (0, 17)
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 180
    MAP_SWIPE_MULTIPLY = 1.445
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.397
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True

        return self.battle_default()

    def battle_7(self):
        return self.fleet_boss.clear_boss()
