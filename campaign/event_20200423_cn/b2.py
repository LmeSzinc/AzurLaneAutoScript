from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger
from campaign.event_20200423_cn.b1 import Config as ConfigBase

MAP = CampaignMap()
MAP.camera_sight = (-4, -2, 5, 3)
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
