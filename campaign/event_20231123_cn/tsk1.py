from .campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('TSK1')
MAP.shape = 'E5'
MAP.camera_data = ['D3']
MAP.camera_data_spawn_point = ['D3']
MAP.map_data = """
    -- ++ ++ ++ --
    -- -- ++ -- --
    -- SP -- MB --
    ++ -- -- -- ++
    -- ++ ++ ++ --
"""
MAP.weight_data = """
    50 50 50 50 50
    50 50 50 50 50
    50 50 50 50 50
    50 50 50 50 50
    50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'boss': 1},
]
A1, B1, C1, D1, E1, \
A2, B2, C2, D2, E2, \
A3, B3, C3, D3, E3, \
A4, B4, C4, D4, E4, \
A5, B5, C5, D5, E5, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    # ===== End of generated config =====

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
    MAP_SWIPE_MULTIPLY = (1.187, 1.209)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.148, 1.169)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.115, 1.135)
    MAP_IS_ONE_TIME_STAGE = True
    FLEET_2 = 0


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        return self.clear_boss()
