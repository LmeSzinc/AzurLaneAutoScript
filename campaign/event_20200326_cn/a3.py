from campaign.event_20200326_cn.a1 import Config
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'G7'
MAP.map_data = '''
    ++ ++ ME ME ME ++ --
    ++ MS -- ME -- MS ++
    ME -- -- __ -- -- ME
    ME -- SP MB SP -- ME
    ME -- -- MB -- -- ME
    -- MS -- MB ++ ++ ++
    ++ -- ME -- ME -- --
'''
MAP.weight_data = """
    10 10 10 10 10 10 10
    10 10 10 10 10 10 10
    10 10 10 10 10 10 10
    10 10 10 10 10 10 10
    10 10 10 10 10 10 10
    10 10 10 10 10 10 10
    10 10 10 20 20 20 20
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'boss': 1},
]


A1, B1, C1, D1, E1, F1, G1, \
A2, B2, C2, D2, E2, F2, G2, \
A3, B3, C3, D3, E3, F3, G3, \
A4, B4, C4, D4, E4, F4, G4, \
A5, B5, C5, D5, E5, F5, G5, \
A6, B6, C6, D6, E6, F6, G6, \
A7, B7, C7, D7, E7, F7, G7, \
    = MAP.flatten()


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True

        if self.clear_enemy(scale=(3,)):
            return True

        return self.battle_default()

    def battle_4(self):
        return self.clear_boss()