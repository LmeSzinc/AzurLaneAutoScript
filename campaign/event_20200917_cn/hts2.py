from module.exception import CampaignEnd
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_base import CampaignBase
from .hts1 import Config as ConfigBase

MAP = CampaignMap('HTS2')
MAP.shape = 'H8'
MAP.camera_data = ['D2', 'D6', 'E2', 'E6']
MAP.camera_data_spawn_point = ['D6']
MAP.map_data = """
    ++ MM -- -- -- -- -- --
    ++ ++ ++ ++ -- -- -- ++
    -- -- -- -- -- ++ -- ++
    -- -- -- ++ ++ ++ -- ++
    -- ++ -- -- ++ -- -- --
    -- -- ++ -- -- ++ -- ++
    -- -- SP ++ MM ++ -- ++
    MM -- -- ++ ++ ++ -- ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
A7, B7, C7, D7, E7, F7, G7, H7, \
A8, B8, C8, D8, E8, F8, G8, H8, \
    = MAP.flatten()


class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = False
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
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
    HOMO_EDGE_COLOR_RANGE = (0, 17)
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.goto(A8, expected='story')
        self.goto(E7, expected='story')
        self.goto(B1, expected='story')
        self.goto(G8, expected='story')

        raise CampaignEnd()
