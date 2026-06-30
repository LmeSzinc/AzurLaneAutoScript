from .campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('SP')
MAP.shape = 'I9'
MAP.camera_data = ['D2', 'D5', 'D7', 'F2', 'F5', 'F7']
MAP.camera_data_spawn_point = ['F6']
MAP.map_data = """
    ++ -- ME ++ ++ ++ ME -- ++
    -- ME -- -- MB -- -- -- ME
    -- -- -- -- -- -- ME -- ++
    ++ ME ++ ++ ++ ++ ++ -- --
    ++ -- ++ ++ ++ ++ ++ ME --
    -- -- ++ ++ ++ SP SP -- --
    ME -- -- -- -- __ __ -- MS
    -- ME -- ++ ME -- ME MS --
    ++ -- ME ++ -- MS ++ -- ++
"""
MAP.weight_data = """
    50 50 50 50 10 10 10 10 10
    50 50 50 50 10 10 10 10 10
    50 50 50 50 10 10 10 10 10
    50 50 50 50 50 50 50 10 10
    50 50 50 50 50 50 50 10 10
    50 50 50 50 50 10 10 10 10
    50 50 50 50 10 10 10 10 10
    50 50 50 50 10 10 10 10 10
    50 50 50 50 10 10 10 10 10
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
MAP.spawn_data_loop = [
    {'battle': 0, 'enemy': 12, 'siren': 3},
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
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = []
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

    STAGE_ENTRANCE = ['half', '20240725']
    MAP_CHAPTER_SWITCH_20241219 = True
    MAP_HAS_MODE_SWITCH = False
    MAP_HAS_MOVABLE_NORMAL_ENEMY = True
    MAP_SIREN_HAS_BOSS_ICON_SMALL = True

    MOVABLE_NORMAL_ENEMY_TURN = (2,)
    MAP_SIREN_MOVE_WAIT = 0.7
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 17),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 17, 255),
        'prominence': 10,
        'distance': 50,
        # 'width': (0, 7),
        'wlen': 1000
    }
    HOMO_EDGE_COLOR_RANGE = (0, 17)
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    MAP_SWIPE_MULTIPLY = (1.090, 1.110)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.054, 1.073)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.023, 1.042)

    MAP_IS_ONE_TIME_STAGE = True
    MAP_WALK_USE_CURRENT_FLEET = True


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(sort=('weight', 'cost_2', 'cost_1')):
            return True

        return self.battle_default()

    def battle_5(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(sort=('weight', 'cost_1')):
            return True

        return self.battle_default()

    def battle_7(self):
        return self.fleet_boss.clear_boss()
