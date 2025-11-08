from .campaign_base import CampaignBaseT as CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('Y.SP')
MAP.shape = 'K10'
MAP.camera_data = ['F4', 'F6']
MAP.camera_data_spawn_point = ['F4']
MAP.map_data = """
    -- -- -- -- -- -- -- -- -- -- --
    -- ++ ++ ++ -- -- -- ++ ++ ++ --
    -- ++ -- ME ++ ++ ++ ME -- ++ --
    -- ++ ME ++ ++ MB ++ ++ ME ++ --
    -- ++ -- -- SP -- SP -- -- ++ --
    -- ++ ME ++ ++ __ ++ ++ ME ++ --
    -- ++ -- ME ++ MS ++ ME -- ++ --
    -- ++ ++ -- MS -- MS -- ++ ++ --
    -- ++ ++ ++ ++ ++ ++ ++ ++ ++ --
    -- -- -- -- -- -- -- -- -- -- --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
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
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, K7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, J8, K8, \
A9, B9, C9, D9, E9, F9, G9, H9, I9, J9, K9, \
A10, B10, C10, D10, E10, F10, G10, H10, I10, J10, K10, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['CAalchemist2', 'BBalchemist2', 'CValchemist2']
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

    MAP_CHAPTER_SWITCH_20241219 = True
    STAGE_ENTRANCE = ['half', '20240725']

    MAP_IS_ONE_TIME_STAGE = True
    HOMO_STORAGE = ((8, 6), [(142.416, 83.7), (1025.571, 83.7), (-16.287, 615.233), (1147.605, 615.233)])
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
    MAP_SWIPE_MULTIPLY = (1.085, 1.105)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.049, 1.068)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.018, 1.037)


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    @staticmethod
    def _campaign_ocr_result_process(result):
        result = CampaignBase._campaign_ocr_result_process(result)
        if result in ['ysp', 'usp', 'iisp', 'ijsp', 'jjsp']:
            result = 'sp'
        return result

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
