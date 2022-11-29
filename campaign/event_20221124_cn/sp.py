from .campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('A.SP')
MAP.shape = 'G8'
MAP.camera_data = ['D3', 'D6']
MAP.camera_data_spawn_point = ['D6']
MAP.map_data = """
    ++ ++ ++ ++ ++ ++ ++
    ++ ++ -- MB -- ++ ++
    -- -- ++ -- ++ -- --
    -- ++ MS __ MS ++ --
    ++ ME -- -- -- ME ++
    ME -- -- MS -- -- ME
    ++ -- -- -- -- -- ++
    ++ -- SP -- SP -- ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 4, 'siren': 3},
    {'battle': 1},
    {'battle': 2},
    {'battle': 3},
    {'battle': 4},
    {'battle': 5},
    {'battle': 6},
    {'battle': 7, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, \
A2, B2, C2, D2, E2, F2, G2, \
A3, B3, C3, D3, E3, F3, G3, \
A4, B4, C4, D4, E4, F4, G4, \
A5, B5, C5, D5, E5, F5, G5, \
A6, B6, C6, D6, E6, F6, G6, \
A7, B7, C7, D7, E7, F7, G7, \
A8, B8, C8, D8, E8, F8, G8, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['BBalchemist', 'CValchemist']
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

    MAP_IS_ONE_TIME_STAGE = True

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 23),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 23, 255),
        'prominence': 10,
        'distance': 50,
        # 'width': (0, 7),
        'wlen': 1000
    }
    HOMO_STORAGE = ((7, 7), [(274.753, 70.34), (1050.178, 70.34), (138.583, 713.524), (1205.781, 713.524)])
    HOMO_EDGE_COLOR_RANGE = (0, 23)
    MAP_SWIPE_MULTIPLY = 1.638
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.584
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'


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
