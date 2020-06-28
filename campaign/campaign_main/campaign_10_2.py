from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger


MAP = CampaignMap('10-2')
MAP.shape = 'H6'
MAP.map_data = '''
    ME -- ME ME -- ++ ME MB
    -- ++ ++ -- ME ++ ME ME
    -- SP ++ ++ __ ME ME ++
    -- SP ++ ++ -- ME ME ++
    -- ++ ++ -- ME ++ ME ME
    -- ME ME ME -- ++ ME MB
'''
MAP.weight_data = '''
    90 90 90 90 90 90 15 10
    90 90 90 90 90 90 10 05
    90 90 90 90 90 30 10 20
    90 90 90 90 90 30 10 20
    90 90 90 50 40 90 10 05
    80 70 60 50 50 90 15 10
'''
# MAP.camera_data = ['D3']
MAP.spawn_data = [
    {'battle': 0, 'enemy': 4},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5},
    {'battle': 6, 'boss': 1},
]

A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
    = MAP.flatten()

road_main = RoadGrids([B6, C6, D6, E5, F4, G2, [G1, H2], G3, G4, G5, [H5, G6]])

class Config:
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 30
    EDGE_LINES_HOUGHLINES_THRESHOLD = 30
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.3
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
        self.fleet_2_push_forward()

        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True

        return self.battle_default()

    def battle_6(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet=2):
                if self.clear_roadblocks([road_main]):
                    return True

        return self.fleet_1.clear_boss()