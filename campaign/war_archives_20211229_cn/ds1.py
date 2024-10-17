from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_base import CampaignBase

MAP = CampaignMap('DS1')
MAP.shape = 'L6'
MAP.camera_data = ['D2', 'D4', 'I2', 'I4']
MAP.camera_data_spawn_point = ['I2', 'I4']
MAP.map_data = """
    ++ ++ -- -- Me -- Me MS -- -- ++ ++
    ++ -- ++ ++ -- -- -- -- ++ ++ ++ ++
    ME -- ME ++ -- ME ++ -- ++ Me -- SP
    ME -- -- -- -- ME ++ -- -- -- -- SP
    -- MB -- ME ++ ++ Me -- __ -- ++ ++
    ME -- ME ++ ++ ++ -- MS ME MS ++ ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2, 'siren': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5, 'enemy': 1},
    {'battle': 6, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, L1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, L2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, L3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, L4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, L5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, L6, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['CL', 'CAgreen', 'CA', 'BB']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
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
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    HOMO_EDGE_COLOR_RANGE = (0, 17)
    MAP_IS_ONE_TIME_STAGE = True
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True

        return self.battle_default()

    def battle_5(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_6(self):
        return self.fleet_boss.clear_boss()
