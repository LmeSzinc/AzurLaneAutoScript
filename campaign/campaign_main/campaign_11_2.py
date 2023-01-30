from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('11-2')
MAP.shape = 'K6'
MAP.camera_data = ['F4', 'G3', 'H4']
MAP.camera_data_spawn_point = ['D4']
MAP.map_data = """
    ++ ++ ++ -- -- ++ -- ME -- Me --
    -- -- -- Me -- __ Me ++ ++ ME --
    SP -- ++ -- -- ME ME MM ++ -- ME
    SP -- ++ -- ME -- ++ ME -- MB MB
    -- ++ ++ ++ __ ME ME -- ++ ++ ++
    -- -- ME -- -- ++ -- ME -- -- MB
"""
MAP.weight_data = """
    90 90 90 90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 10 05 90 90
    90 90 90 90 90 25 20 15 90 90 90
    90 90 90 40 35 30 90 90 90 90 90
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
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, \
    = MAP.flatten()

road_main = RoadGrids([C6, F5, G5, H4, H6])


class Config:
    DETECTION_BACKEND = 'homography'
    HOMO_STORAGE = ((6, 6), [(579.064, 82.271), (1248.248, 82.271), (562.795, 616.581), (1438.283, 616.581)])
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
            if not self.check_accessibility(boss[0], fleet='boss'):
                if self.clear_roadblocks([road_main]):
                    return True

        return self.fleet_boss.clear_boss()

    def handle_boss_appear_refocus(self, preset=(-3, -2)):
        return super().handle_boss_appear_refocus(preset)
