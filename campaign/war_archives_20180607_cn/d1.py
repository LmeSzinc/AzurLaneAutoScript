from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from ..campaign_war_archives.campaign_base import CampaignBase

MAP = CampaignMap('D1')
MAP.camera_sight = (-4, -2, 4, 2)
MAP.shape = 'J7'
# MAP.camera_data = ['D2', 'D5', 'G2', 'G5']
MAP.camera_data_spawn_point = []
MAP.map_data = """
    ++ ++ ++ MS -- ME ++ ++ ++ ++
    ++ ++ ++ -- ME __ -- ++ ++ ++
    ++ ++ ++ __ -- ME -- -- ++ ++
    ++ ++ ++ Me ++ ++ ME -- ++ ++
    -- MB -- -- ME ME -- ME -- SP
    -- -- Me -- -- -- -- __ -- SP
    ++ ++ -- Me MS ME Me ++ ME --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
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
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, \
    = MAP.flatten()


class Config:
    SUBMARINE = 0

    POOR_MAP_DATA = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_SIREN = True
    MAP_HAS_DYNAMIC_RED_BORDER = False
    MAP_SIREN_COUNT = 3
    MAP_HAS_PT_BONUS = True

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (100, 255 - 24),
        'width': 1,
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 24, 255),
        'prominence': 2,
        'distance': 50,
        'wlen': 1000
    }
    VANISH_POINT_RANGE = ((540, 740), (-4000, -2000))
    DISTANCE_POINT_X_RANGE = ((-2000, -1000),)
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 50
    EDGE_LINES_HOUGHLINES_THRESHOLD = 50
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.
    MID_DIFF_RANGE_H = (45, 70)
    MID_DIFF_RANGE_V = (97 - 3, 97 + 3)
    TRUST_EDGE_LINES = True
    MAP_GRID_CENTER_TOLERANCE = 0.3


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
