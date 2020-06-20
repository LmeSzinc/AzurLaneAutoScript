from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('13-4')
MAP.shape = 'K8'
MAP.map_data = '''
    MB ME ME -- ME ++ ++ ++ MB MB ++
    MB -- ME ME ME -- -- MA -- ME ++
    ME -- -- ME ME -- ME ME -- ME ME
    ++ SP -- ME ++ ME -- -- -- -- ME
    ++ SP ME -- ME -- -- ME ++ ++ --
    ++ -- -- -- ME -- ME ME ++ ++ ME
    ME ME ME -- -- -- ME -- -- ME --
    -- ME ME ME -- -- ++ ++ -- ME --
'''
# MAP.weight_data = '''
#     10 30 30 10 10 10 10 10 10
#     5 30 10 30 10 10 5 10 10
#     10 10 5 4 30 10 5 30 10
#     10 10 10 10 10 10 5 10 30
#     10 10 10 10 10 10 10 30 10
#     10 10 10 10 30 10 5 10 10
# '''

MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'enemy': 1},
    {'battle': 6,},
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


class Config:

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


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_enemy():
            return True
        return self.battle_default()

    def battle_4(self):
        if self.fleet_2.clear_enemy():
            return True
        return self.battle_default()

    def battle_6(self):
        self.pick_up_ammo()
        if self.fleet_1.clear_enemy():
            return True

    def battle_7(self):
        return self.fleet_boss.clear_boss()