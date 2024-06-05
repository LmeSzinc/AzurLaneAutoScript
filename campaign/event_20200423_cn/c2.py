from campaign.event_20200423_cn.c1 import Config
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.map_data = '''
    -- -- ME -- ME -- MB
    ME -- -- ++ ++ ++ --
    -- ME __ -- ME ME --
    ME -- ++ MS -- -- --
    -- -- -- -- -- -- --
    SP -- -- -- ME ++ --
    SP SP -- ME -- ++ MB
'''
MAP.camera_data = ['D3', 'D5']
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'boss': 1},
]


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(scale=(1, 2)):
            return True

        return self.battle_default()

    def battle_4(self):
        return self.brute_clear_boss()