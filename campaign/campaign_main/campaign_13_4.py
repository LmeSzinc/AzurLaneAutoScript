from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_13_1 import Config as ConfigBase

MAP = CampaignMap('13-4')
MAP.shape = 'K8'
MAP.camera_data = ['D2', 'D4', 'D6', 'H2', 'H4', 'H6']
MAP.camera_data_spawn_point = ['D2', 'D6']
MAP.map_data = """
    MB ME ME -- ME ++ ++ ++ MB MB ++
    MB __ ME ME ME -- __ MA -- Me ++
    ME -- -- Me Me -- Me Me -- Me ME
    ++ SP -- ME ++ Me -- -- -- -- ME
    ++ SP ME -- ME -- -- ME ++ ++ --
    ++ -- -- -- Me -- ME Me ++ ++ ME
    ME ME Me -- -- -- Me -- -- ME --
    -- ME Me ME -- -- ++ ++ -- ME --
"""
MAP.weight_data = """
    50 50 90 90 90 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    90 50 50 50 50 50 50 50 50 90 50
    90 90 50 50 50 50 50 50 50 90 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 3},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 2},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'enemy': 1},
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
    = MAP.flatten()


class Config(ConfigBase):
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5
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


# step_on = SelectedGrids([A7, B1, B7, C7, D2, D3, G7, J2, K4, K6])
# road_main = RoadGrids([A7, B1, B7, C7, D2, D3, [G7, J2], K4, K6])

class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_filter_enemy('1L > 1M > 2L > 2M > 3L > 2E > 3E > 2C > 3C > 3M', preserve=0):
            return True

        return self.battle_default()

    def battle_3(self):
        self.pick_up_ammo()

        if self.clear_filter_enemy('1L > 1M > 2L > 2M > 3L > 2E > 3E > 2C > 3C > 3M', preserve=0):
            return True

        return self.battle_default()

    def battle_7(self):
        return self.fleet_boss.clear_boss()
