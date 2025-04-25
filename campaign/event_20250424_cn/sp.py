from .campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('SP')
MAP.shape = 'M5'
MAP.camera_data = ['F3', 'H3']
MAP.camera_data_spawn_point = ['F3']
MAP.map_data = """
    ++ ++ ++ ++ ++ ++ ++ ++ ME -- ME ++ ++
    -- -- ++ SP -- -- MS ME -- Me -- ++ ++
    -- -- MB -- __ MS -- -- -- -- -- ++ --
    -- -- ++ SP -- -- MS ME -- Me -- ++ ++
    ++ ++ ++ ++ ++ ++ ++ ++ ME -- ME ++ ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50
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
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, L1, M1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, L2, M2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, L3, M3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, L4, M4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, L5, M5, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['Intruder']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    # ===== End of generated config =====

    MAP_CHAPTER_SWITCH_20241219_SP = True
    STAGE_ENTRANCE = ['half', '20240725']
    MAP_IS_ONE_TIME_STAGE = True
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
        # 'width': (0, 7),
        'wlen': 1000
    }
    HOMO_EDGE_COLOR_RANGE = (0, 17)
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 300
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom-right'
    MAP_SWIPE_MULTIPLY = (1.206, 1.228)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.166, 1.188)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.132, 1.152)


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
