from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_base import CampaignBase

MAP = CampaignMap('SP')
MAP.shape = 'K9'
# MAP.camera_data = ['D2', 'D6', 'D7', 'H2', 'H6', 'H7']
# MAP.camera_data_spawn_point = ['D2', 'H2']
MAP.camera_data = ['F2', 'F4', 'F7']
MAP.camera_data_spawn_point = ['F2']
MAP.portal_data = [('E1', 'K1'), ('K1', 'E1'), ('A1', 'G1'), ('G1', 'A1')]
MAP.map_data = """
    -- -- MS ++ -- -- -- ++ MS -- --
    -- -- -- ++ -- __ -- ++ -- -- --
    ++ -- Me ++ SP -- SP ++ Me -- ++
    -- ++ ++ ++ ++ -- ++ ++ ++ ++ --
    -- -- ++ ME -- -- -- ME ++ -- --
    -- -- ++ -- -- MS -- -- ++ -- --
    -- ++ ++ ++ ++ -- ++ ++ ++ ++ --
    ++ -- -- -- ++ -- ++ -- -- -- ++
    -- -- -- -- ++ MB ++ -- -- -- --
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
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1},
    {'battle': 2},
    {'battle': 3},
    {'battle': 4, 'enemy': 2, 'siren': 1},
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
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = False
    MAP_HAS_PORTAL = True
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    # ===== End of generated config =====

    STAGE_ENTRANCE = ['blue']
    MAP_SIREN_TEMPLATE = ['CV', 'BB']
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = False

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (150, 255 - 24),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 24, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }
    HOMO_EDGE_COLOR_RANGE = (0, 24)
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.82
    MAP_SWIPE_MULTIPLY = 1.88


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True

        return self.battle_default()

    def battle_7(self):
        return self.fleet_boss.clear_boss()
