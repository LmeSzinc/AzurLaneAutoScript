from campaign.event_20200423_cn.d1 import Config as ConfigBase
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.map_data = '''
    -- -- -- -- SP SP -- -- ++ ++
    -- -- -- -- -- -- -- -- ++ ++
    ++ ++ ++ -- -- -- -- -- -- --
    -- -- -- -- ++ ++ -- -- -- --
    -- -- -- -- -- -- -- -- -- --
    -- ++ -- -- -- -- ++ -- -- --
    -- ++ -- -- -- -- -- -- -- --
'''


class Config(ConfigBase):
    FLEET_BOSS = 2


class Campaign(CampaignBase):
    MAP = MAP
