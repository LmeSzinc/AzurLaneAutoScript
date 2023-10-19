from campaign.event_20200507_cn.sp1 import Config
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.map_data = '''
    -- -- ++ ++ -- ME -- ++ ++ ME --
    ME ME ++ ++ ME -- ME -- ME -- ME
    ME -- MB -- MB -- -- -- -- -- --
    ++ -- MB MB -- __ ME ++ ++ ME ++
    SP -- ME -- ME -- -- ++ ME -- ME
    SP SP ++ ++ ++ ME -- -- -- -- ME
'''
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'boss': 1},
]


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        return self.battle_default()

    def battle_4(self):
        return self.brute_clear_boss()
