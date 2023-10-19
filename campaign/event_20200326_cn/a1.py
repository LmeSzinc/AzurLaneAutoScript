from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'F7'
MAP.map_data = '''
    -- -- ME -- -- ++
    ME ++ ++ ME -- ME
    -- ++ MS -- SP --
    MB MB __ -- -- ME
    ME MB MS -- SP --
    -- ++ ME ME -- --
    ME ++ ME ME ++ ME
'''
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1, 'boss': 1},
]


A1, B1, C1, D1, E1, F1, \
A2, B2, C2, D2, E2, F2, \
A3, B3, C3, D3, E3, F3, \
A4, B4, C4, D4, E4, F4, \
A5, B5, C5, D5, E5, F5, \
A6, B6, C6, D6, E6, F6, \
A7, B7, C7, D7, E7, F7, \
    = MAP.flatten()


class Config:
    MAP_HAS_AMBUSH = False
    CAMPAIGN_MODE = 'normal'

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (50, 255 - 80),
        'width': 1,
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 80, 255),
        'prominence': 10,
        'distance': 50,
        'width': (0, 7),
        'wlen': 1000
    }


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True

        if self.clear_enemy(scale=(3,)):
            return True

        return self.battle_default()

    def battle_3(self):
        return self.clear_boss()
