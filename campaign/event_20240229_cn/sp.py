from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('SP')
MAP.shape = 'T10'
MAP.camera_data = ['B3', 'B6']
MAP.camera_data_spawn_point = ['B6']
MAP.map_data = """
    -- ++ ++ ++ -- -- -- -- ++ ++ -- -- -- -- -- -- -- -- -- --
    ME -- MB -- ME -- -- -- ++ ++ ++ -- ++ -- -- -- ++ ++ ++ --
    -- ME __ ME -- -- ++ -- -- -- ++ -- -- -- ++ -- -- -- -- --
    ME -- MS -- ME -- -- -- -- -- -- -- -- -- ++ -- -- -- -- ++
    -- ME -- ME -- -- -- -- -- ++ ++ ++ -- -- -- -- ++ -- -- --
    MS -- -- -- MS -- ++ -- -- -- -- -- -- ++ ++ -- -- -- -- --
    -- -- -- -- -- -- -- -- ++ -- -- -- -- -- ++ -- -- ++ ++ --
    ++ SP -- SP ++ ++ -- -- -- -- ++ ++ -- -- -- -- -- ++ ++ --
    -- -- -- -- -- ++ -- ++ ++ -- -- ++ -- ++ ++ ++ -- -- -- --
    ++ ++ ++ -- -- -- -- -- -- -- -- -- -- -- ++ -- -- -- ++ --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 8, 'siren': 3},
    {'battle': 1},
    {'battle': 2},
    {'battle': 3},
    {'battle': 4},
    {'battle': 5},
    {'battle': 6},
    {'battle': 7, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, L1, M1, N1, O1, P1, Q1, R1, S1, T1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, L2, M2, N2, O2, P2, Q2, R2, S2, T2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, L3, M3, N3, O3, P3, Q3, R3, S3, T3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, L4, M4, N4, O4, P4, Q4, R4, S4, T4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, L5, M5, N5, O5, P5, Q5, R5, S5, T5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, L6, M6, N6, O6, P6, Q6, R6, S6, T6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, K7, L7, M7, N7, O7, P7, Q7, R7, S7, T7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, J8, K8, L8, M8, N8, O8, P8, Q8, R8, S8, T8, \
A9, B9, C9, D9, E9, F9, G9, H9, I9, J9, K9, L9, M9, N9, O9, P9, Q9, R9, S9, T9, \
A10, B10, C10, D10, E10, F10, G10, H10, I10, J10, K10, L10, M10, N10, O10, P10, Q10, R10, S10, T10, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['shuguangjixie_shanliu', 'shuguangjixie_huixing']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    # ===== End of generated config =====

    MAP_IS_ONE_TIME_STAGE = True
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom-left'
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
    MAP_SWIPE_MULTIPLY = (0.996, 1.014)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (0.963, 0.981)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (0.935, 0.952)


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=2):
            return True

        return self.battle_default()

    def battle_5(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_7(self):
        return self.fleet_boss.clear_boss()
