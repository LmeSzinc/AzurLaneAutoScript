from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_base import CampaignBase
from .sp1 import Config as ConfigBase

MAP = CampaignMap('SP4')
MAP.shape = 'I8'
MAP.camera_data = ['D2', 'D4', 'D6', 'F2', 'F4', 'F6']
MAP.camera_data_spawn_point = ['F6', 'D6']
MAP.map_data = """
    ++ ++ ++ ME -- ME ++ ++ ++
    ME -- ++ -- MB -- ++ -- ME
    ++ ME Me -- Me -- Me ME ++
    ME -- ME MS ++ MS ME -- ME
    ++ ++ -- -- ++ -- -- ++ ++
    ++ ++ -- MS __ MS -- ++ ++
    ME -- Me -- ME -- Me -- ME
    -- ME ++ SP -- SP ++ ME --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 40 10 50 10 40 50 50
    50 50 45 20 50 20 45 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 40 50 50 50 40 50 50
    50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3, 'siren': 2},
    {'battle': 1, 'enemy': 2, 'siren': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4},
    {'battle': 5, 'boss': 1},
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


class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['AzusaMiura', 'ChihayaKisaragi', 'IoriMinase']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    # ===== End of generated config =====

    MAP_SWIPE_MULTIPLY = 1.541
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.490
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    DETECTION_BACKEND = 'perspective'
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    TRUST_EDGE_LINES = False
    TRUST_EDGE_LINES_THRESHOLD = 7

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 24),
        'width': (1.5, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 10, 255),
        'width': (1.5, 10),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.fleet_2_push_forward()

        if self.clear_siren(genre=('Siren_AzusaMiura', 'Siren_IoriMinase')):
            return True
        if self.clear_enemy(scale=(1,)):
            return True
        if self.clear_enemy(scale=(2,)):
            return True
        if self.clear_enemy(scale=(3,)):
            return True

        return self.battle_default()

    def battle_5(self):
        return self.fleet_boss.clear_boss()
