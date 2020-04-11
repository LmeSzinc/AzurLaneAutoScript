from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap()
MAP.shape = 'G1'
MAP.map_data = '''
    SP -- -- -- -- ME MB
'''
MAP.spawn_data = [
    {'battle': 0, 'enemy': 1},
    {'battle': 1, 'boss': 1},
]

A1, B1, C1, D1, E1, F1, G1, \
    = MAP.flatten()

class Config:
    FLEET_2 = 0
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (120, 255 - 40),
        'width': (1.5, 10),
        'prominence': 10,
        'distance': 35,
    }
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40

class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        return self.battle_default()

    def battle_1(self):
        return self.clear_boss()
