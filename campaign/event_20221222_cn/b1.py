from .campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('B1')
MAP.shape = 'I8'
MAP.camera_data = ['D2', 'D6', 'F2', 'F6']
MAP.camera_data_spawn_point = ['D6']
MAP.map_data = """
    -- ME ++ -- Me -- Me ++ ++
    ME -- -- -- -- ME -- MB ++
    -- -- MS -- -- -- __ -- Me
    Me -- ME ++ MS Me -- -- Me
    -- -- -- ++ ++ ++ -- ME --
    -- -- -- ME -- ME MS -- --
    SP -- -- -- MS -- ME -- ME
    ++ SP -- ME ++ ++ ++ ME --
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
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2, 'boss': 1},
    {'battle': 5, 'enemy': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = []
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====

    MAP_SIREN_HAS_BOSS_ICON_SMALL = True
    MAP_ENEMY_TEMPLATE = ['Light20221222', 'Main20221222', 'Carrier20221222']
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 33),
        'width': (1.5, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 33, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }
    HOMO_EDGE_COLOR_RANGE = (0, 33)
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 300
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    MAP_SWIPE_MULTIPLY = (1.028, 1.047)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (0.994, 1.013)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (0.965, 0.983)


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 2L > 2M > 3L > 3M > 1E > 2E > 3E > 1C > 2C > 3C'

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_4(self):
        return self.clear_boss()
