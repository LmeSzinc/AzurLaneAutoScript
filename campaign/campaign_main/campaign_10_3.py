from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('10-3')
MAP.shape = 'I6'
MAP.camera_data = ['D2', 'E3', 'F4']
MAP.camera_data_spawn_point = ['E3']
MAP.map_data = """
    Me -- ME -- ME MB ++ -- MM
    -- ++ ++ ++ ME MB ++ -- --
    -- Me -- ME ME ME __ ME --
    -- -- ++ ++ MB ME ME Me ++
    -- -- SP SP ++ ++ ++ ME MB
    ++ -- -- -- Me -- ME ME ME
"""
MAP.weight_data = """
    90 90 90 90 40 10 90 90 90
    90 90 90 90 30 10 90 90 90
    90 90 90 90 20 05 20 90 90
    90 90 90 90 10 15 20 30 90
    90 90 90 90 90 90 90 40 40
    90 90 90 90 80 70 60 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 4},
    {'battle': 1, 'enemy': 2, 'mystery': 1},
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
    = MAP.flatten()

road_main = RoadGrids([E6, G6, H6, E5, H4, G4, F4, F3])


class Config:
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 35
    EDGE_LINES_HOUGHLINES_THRESHOLD = 35
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
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.fleet_2_push_forward()

        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True

        self.clear_all_mystery()

        return self.battle_default()

    def battle_6(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                if self.clear_roadblocks([road_main]):
                    return True

        return self.fleet_boss.clear_boss()
