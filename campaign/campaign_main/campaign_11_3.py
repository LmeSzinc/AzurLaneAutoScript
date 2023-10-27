from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('11-3')
MAP.shape = 'I7'
MAP.camera_data = ['D3', 'F5']
MAP.camera_data_spawn_point = ['D5']
MAP.map_data = """
    ++ -- -- ME -- Me ++ ++ ++
    __ ME ME -- Me -- ME -- __
    -- -- ME -- -- ME -- ME --
    MB ++ ++ -- ++ ++ ++ -- ME
    ++ ++ ++ MB -- ME __ ME --
    SP -- -- Me -- ME ++ ME --
    SP -- -- -- ++ -- ME -- MB
"""
MAP.weight_data = """
    90 90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 90 90
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5},
    {'battle': 6, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, \
    = MAP.flatten()

road_main = RoadGrids([C2, D6, F6, G7])


class Config:
    DETECTION_BACKEND = 'homography'
    HOMO_STORAGE = ((5, 4), [(133.207, 81.356), (696.903, 81.356), (44.566, 406.051), (705.278, 406.051)])
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 30
    EDGE_LINES_HOUGHLINES_THRESHOLD = 30
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.2
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
        'width': (0, 10),
        'wlen': 1000,
    }


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True

        return self.battle_default()

    def battle_6(self):
        if self.clear_roadblocks([road_main]):
            return True
        return self.fleet_boss.clear_boss()
