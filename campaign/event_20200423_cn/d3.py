from campaign.event_20200423_cn.d1 import Config as ConfigBase
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.map_data = '''
    MS -- -- ME -- MS -- ME --
    -- ME -- -- __ ME -- ++ ++
    ++ ++ -- ME ++ ++ ME -- ME
    MB -- -- -- ++ ++ -- -- SP
    ++ ++ -- -- -- -- -- -- SP
    ME -- ME ME ME -- -- ++ --
    -- ME ++ ++ ++ MS ME -- --
'''
MAP.weight_data = '''
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    20 20 10 10 10 10 10 10 10
    20 20 10 10 10 10 10 10 10
'''
MAP.camera_data = ['D3', 'D5', 'F3', 'F5']
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2, 'siren': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5, 'enemy': 1},
    {'battle': 6, 'boss': 1},
]


class Config(ConfigBase):
    FLEET_BOSS = 2


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(scale=(2, 3)):
            return True

        return self.battle_default()

    def battle_5(self):
        if self.clear_enemy(scale=(1,)):
            return True
        if self.clear_enemy(scale=(2,)):
            return True

        return self.battle_default()

    def battle_6(self):
        return self.fleet_boss.clear_boss()
