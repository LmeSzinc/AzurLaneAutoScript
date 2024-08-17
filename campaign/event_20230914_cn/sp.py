from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('SP')
MAP.shape = 'H5'
MAP.camera_data = ['E3']
MAP.camera_data_spawn_point = ['C3']
MAP.map_data = """
    -- ++ ++ ++ ++ -- ME --
    SP -- -- -- ++ ME -- ME
    -- -- MB -- -- -- -- ++
    SP -- -- -- ++ ME -- ME
    -- ++ ++ ++ ++ -- ME --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 6},
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
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    # ===== End of generated config =====

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
        'wlen': 1000
    }
    HOMO_STORAGE = ((9, 7), [(158.102, 59.806), (1142.124, 59.806), (-34.052, 695.951), (1324.267, 695.951)])
    HOMO_EDGE_COLOR_RANGE = (0, 17)
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom-right'
    MAP_IS_ONE_TIME_STAGE = True

    MAP_SWIPE_MULTIPLY = (1.229, 1.253)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.189, 1.211)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.154, 1.175)


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    _is_a2 = False

    def battle_0(self):
        if self.fleet_at(A2):
            self._is_a2 = True
        self.goto(B3)
        self.clear_chosen_enemy(C3)

        return True

    def battle_1(self):
        if self._is_a2:
            self.clear_chosen_enemy(B4)
        else:
            self.clear_chosen_enemy(B2)

        return True

    def battle_2(self):
        if self._is_a2:
            self.goto(C3)
            self.clear_chosen_enemy(D3)
        else:
            self.clear_chosen_enemy(D2)

        return True

    def battle_3(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_7(self):
        return self.fleet_boss.clear_boss()
