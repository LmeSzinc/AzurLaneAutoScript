from campaign.event_20200507_cn.sp1 import Config as ConfigBase
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.map_data = '''
    ++ ++ ++ ME ME ++ MB MB
    ME -- -- -- -- ME -- MB
    -- -- ME ME -- __ -- ++
    ME -- ++ ++ -- ME -- ME
    -- -- SP SP -- ++ -- ME
    ME -- -- -- ME ++ ME --
    ++ ++ ME -- -- -- -- ME
    ++ ME ME -- ME ++ ME --
'''
MAP.camera_data = ['D3', 'D6']
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'boss': 1},
]


class Config(ConfigBase):
    FLEET_BOSS = 2


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_enemy(scale=(2,)):
            return True
        if self.clear_enemy(scale=(1,)):
            return True

        return self.battle_default()

    def battle_5(self):
        return self.brute_clear_boss()
