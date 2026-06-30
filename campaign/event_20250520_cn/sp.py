from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('SP')
MAP.shape = 'I10'
MAP.camera_data = ['E6', 'E8']
MAP.camera_data_spawn_point = ['E8']
MAP.map_data = """
    -- -- -- -- -- -- -- -- --
    -- ++ -- ++ ++ ++ -- ++ --
    ++ -- -- ++ ++ ++ -- -- --
    -- -- -- ++ ++ ++ -- -- ++
    -- -- ME -- MB -- ME -- --
    -- ME -- MS -- MS -- ME ++
    -- ++ ME -- MS -- ME ++ ++
    -- ++ -- -- __ -- -- ++ ++
    ++ ME -- SP -- SP -- ME --
    -- -- ME ++ ++ ++ ME -- --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 10, 'siren': 3},
    {'battle': 1},
    {'battle': 2},
    {'battle': 3},
    {'battle': 4},
    {'battle': 5},
    {'battle': 6},
    {'battle': 7, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, \
A9, B9, C9, D9, E9, F9, G9, H9, I9, \
A10, B10, C10, D10, E10, F10, G10, H10, I10, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['RoyalOak', 'Victorious']
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

    MAP_CHAPTER_SWITCH_20241219 = True
    STAGE_ENTRANCE = ['half', '20240725']
    MAP_IS_ONE_TIME_STAGE = True

    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (120, 255 - 17),
        'width': (1.5, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 17, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }
    HOMO_STORAGE = ((9, 6), [(205.118, 96.796), (1192.803, 96.796), (71.385, 634.321), (1407.083, 634.321)])
    HOMO_EDGE_COLOR_RANGE = (0, 17)
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210
    MAP_HAS_MOVABLE_NORMAL_ENEMY = True
    MAP_SIREN_MOVE_WAIT = 0.5
    MAP_WALK_USE_CURRENT_FLEET = True
    MAP_SWIPE_MULTIPLY = (1.014, 1.033)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (0.981, 0.999)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (0.952, 0.970)


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
