from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger


MAP = CampaignMap()
MAP.shape = 'F4'
MAP.map_data = '''
    -- SP ME -- ME --
    SP -- ++ ++ ME MM
    ++ -- ME -- ME ME
    ++ ++ ++ MB -- ++
'''
MAP.weight_data = '''
    40 40 40 40 40 40
    30 30 30 30 30 30
    20 20 20 20 20 30
    10 10 10 10 10 10
'''
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'mystery': 1},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 2, 'boss': 1},
]

A1, B1, C1, D1, E1, F1, \
A2, B2, C2, D2, E2, F2, \
A3, B3, C3, D3, E3, F3, \
A4, B4, C4, D4, E4, F4, \
    = MAP.flatten()


class Config:
    FLEET_BOSS = 1

    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (120, 255 - 40),
        'width': (1.5, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 40, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.clear_all_mystery()

        return self.battle_default()

    def battle_2(self):
        self.clear_all_mystery()

        if not self.check_accessibility(D4, fleet='boss'):
            return self.battle_default()

        return self.fleet_boss.clear_boss()

    def handle_boss_appear_refocus(self, preset=(0, -2)):
        return super().handle_boss_appear_refocus(preset)
