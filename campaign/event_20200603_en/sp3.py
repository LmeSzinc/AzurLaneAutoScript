from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('sp3')
MAP.shape = 'i6'
MAP.map_data = '''
    ++ MB -- ME -- ME -- ++ ++
    MB -- ME -- ++ -- ME ++ ++
    MB ME -- ME -- ME -- ME --
    ++ ++ ++ -- ME -- ME ++ --
    MB -- ME ME -- ++ -- -- SP
    -- ME -- -- -- ++ -- SP SP
'''
MAP.camera_data = ['D3', 'F5']
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'boss': 1},
]


class Config:
    SUBMARINE = 0
    FLEET_BOSS = 0
    MAP_HAS_AMBUSH = False
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        return self.battle_default()

    def battle_5(self):
        return self.brute_clear_boss()
