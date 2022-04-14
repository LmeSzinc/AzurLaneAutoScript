from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('8-1')
MAP.shape = 'I3'
MAP.camera_data = ['D1', 'F1']
MAP.camera_data_spawn_point = ['D1', 'F1']
MAP.map_data = """
    SP -- ++ ++ ME -- ME MB ++
    SP -- ++ ++ ME -- ME -- ME
    -- ME ME -- ME ++ ME ME MB
"""
MAP.weight_data = """
    50 50 50 50 50 50 21 30 50
    50 50 50 50 25 24 20 12 11
    50 45 40 31 30 50 22 10 20
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
    = MAP.flatten()


class Config:
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 35
    EDGE_LINES_HOUGHLINES_THRESHOLD = 35
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.3
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (120, 255 - 49),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 49, 255),
        'prominence': 10,
        'distance': 50,
        'width': (0, 10),
        'wlen': 1000,
    }
    HOMO_EDGE_COLOR_RANGE = (0, 49)
    MAP_SWIPE_MULTIPLY = 1.722


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.fleet_2_push_forward()

        return self.battle_default()

    def battle_4(self):
        return self.brute_clear_boss()
