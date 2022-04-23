from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('SP')
MAP.shape = 'M10'
MAP.camera_data = ['D5', 'D8', 'J5', 'J8']
MAP.camera_data_spawn_point = ['D8', 'J8']
MAP.map_data = """
    -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- ++ ++ -- -- -- -- -- --
    -- ++ ++ ++ -- -- ++ -- -- ++ ++ ++ --
    -- ME ++ ++ ++ ++ ++ ++ ++ ++ ++ Me --
    Me -- Me -- ++ ++ ++ ++ ++ -- Me -- Me
    -- -- -- MS Me -- ++ -- Me MS -- -- --
    -- ME -- -- -- ++ MB ++ -- -- -- ME --
    ME -- ME -- -- MS -- MS -- -- ME -- ME
    -- ME -- -- -- -- __ -- -- -- -- ME --
    -- -- -- SP -- -- -- -- -- SP -- -- --
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
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2, 'siren': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2},
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
    MAP_SIREN_TEMPLATE = ['Scharnhorst', 'Deutschland', 'Spee', 'Gneisenau', 'Tirpitz']
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

    DETECTION_BACKEND = 'homography'
    HOMO_STORAGE = ((10, 6), [(172.714, 96.467), (1291.455, 96.467), (27.369, 639.803), (1491.921, 639.803)])
    HOMO_EDGE_COLOR_RANGE = (0, 13)
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 350
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    MAP_SWIPE_MULTIPLY = 1.472
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.423


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
