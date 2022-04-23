from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .b1 import Config as ConfigBase

MAP = CampaignMap('B3')
MAP.in_map_swipe_preset_data = (1, 1)
MAP.shape = 'I10'
MAP.camera_data = ['E3', 'E5', 'C6', 'F6']
MAP.camera_data_spawn_point = ['E7']
MAP.map_data = """
    ++ ++ -- -- Me -- -- ++ ++
    ++ -- -- ME __ ME -- -- ++
    -- -- Me -- MS -- Me -- --
    -- ME -- ++ -- ++ -- ME --
    -- -- MS -- MB -- MS -- --
    -- ME -- ++ -- ++ -- ME --
    -- -- Me -- MS -- Me -- --
    ME -- -- -- -- -- -- -- ME
    ++ ++ -- SP -- SP -- ++ ++
    ++ ++ -- -- -- -- -- ++ ++
"""
MAP.weight_data = """
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5, 'enemy': 1, 'boss': 1},
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
A10, B10, C10, D10, E10, F10, G10, H10, I10, \
    = MAP.flatten()


class Config(ConfigBase):
    MAP_SIREN_TEMPLATE = ['ELpurple', 'CLpurple', 'CApurple']

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 40),
        'width': (0.9, 50),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 24, 255),
        'prominence': 2,
        'distance': 50,
        'wlen': 1000
    }
    MID_DIFF_RANGE_H = (144 - 3, 144 + 3)
    MID_DIFF_RANGE_V = (144 - 3, 144 + 3)
    # Grid have 1.2x width, images on the grid still remain the same.
    # Both homography and perspective are usable, but perspective is less effected by this.
    DETECTION_BACKEND = 'homography'
    HOMO_STORAGE = ((7, 5), [(198.047, 82.241), (1078.103, 82.241), (93.21, 506.071), (1183.061, 506.071)])
    HOMO_TILE = (168, 140)
    HOMO_CENTER_OFFSET = (48 + 14, 48)
    GRID_IMAGE_A_MULTIPLY = 1 / 1.2
    MAP_SWIPE_MULTIPLY = 1.537


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True

        return self.battle_default()

    def battle_5(self):
        return self.fleet_1.clear_boss()
