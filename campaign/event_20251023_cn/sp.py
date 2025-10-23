from .campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('SP')
MAP.shape = 'T3'
MAP.camera_data = ['I1', 'P1', 'Q1']
MAP.camera_data_spawn_point = ['I1']
MAP.map_data = """
    ++ ++ ++ ++ -- -- -- SP ++ ME ++ ++ ME -- -- -- ME ++ ME --
    ++ ++ ++ ++ -- MB __ -- MS -- ++ ++ -- -- ++ -- -- -- -- ME
    ++ ++ ++ ++ -- -- -- SP ++ MS -- MS -- ME ++ ME -- ++ ME --
"""
MAP.weight_data = """
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
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = []
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = False
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    # ===== End of generated config =====

    STAGE_ENTRANCE = ['half', '20240725']
    MAP_CHAPTER_SWITCH_20241219 = True
    HOMO_STORAGE = ((10, 5), [(152.845, 95.044), (1264.11, 95.044), (28.172, 525.208), (1419.191, 525.208)])
    HOMO_EDGE_COLOR_RANGE = (0, 33)
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 120

    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'right'
    MAP_IS_ONE_TIME_STAGE = True

    MAP_SWIPE_MULTIPLY = (1.252, 1.276)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.211, 1.233)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.176, 1.197)


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def map_data_init(self, map_):
        super().map_data_init(map_)
        I2.is_siren = True
        J3.is_siren = True
        L3.is_siren = True

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
