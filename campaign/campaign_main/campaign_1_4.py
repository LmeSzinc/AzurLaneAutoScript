from campaign.campaign_main.campaign_1_1 import Config
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'G3'
MAP.camera_data = ['D1']
MAP.camera_data_spawn_point = ['D1']
MAP.map_data = """
    SP -- ME -- ++ ++ ++
    ++ ++ ME -- MA ++ ++
    ++ ++ ++ ME -- ME MB
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2},
    {'battle': 3, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, \
A2, B2, C2, D2, E2, F2, G2, \
A3, B3, C3, D3, E3, F3, G3, \
    = MAP.flatten()


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        return self.battle_default()

    def battle_3(self):
        return self.clear_boss()
