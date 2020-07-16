from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger
from campaign.event_20200716_en.a1 import Config as ConfigBase

MAP = CampaignMap('A2')
MAP.camera_sight = (-4, -2, 4, 2)
MAP.shape = 'F7'
# MAP.camera_data = ['C2', 'C5']
MAP.camera_data_spawn_point = []
MAP.map_data = """
    ++ ++ ME -- Me MB
    ++ ++ -- -- -- --
    ++ ++ ME -- ME Me
    ME -- ME MS -- --
    -- ME -- -- Me MB
    SP -- ME -- ++ ++
    SP SP -- ME ++ ++
"""
MAP.weight_data = """
    10 10 10 10 10 10
    10 10 10 10 10 10
    10 10 10 10 10 10
    10 10 10 10 10 10
    10 10 10 10 10 10
    10 10 10 10 10 10
    10 10 10 10 10 10
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2, 'boss': 1},
    {'battle': 5, 'enemy': 1},
]
A1, B1, C1, D1, E1, F1, \
A2, B2, C2, D2, E2, F2, \
A3, B3, C3, D3, E3, F3, \
A4, B4, C4, D4, E4, F4, \
A5, B5, C5, D5, E5, F5, \
A6, B6, C6, D6, E6, F6, \
A7, B7, C7, D7, E7, F7, \
    = MAP.flatten()


class Config(ConfigBase):
    pass


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        return self.battle_default()

    def battle_4(self):
        return self.fleet_boss.clear_boss()
