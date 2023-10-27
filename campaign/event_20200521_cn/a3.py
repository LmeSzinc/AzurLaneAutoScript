from campaign.event_20200521_cn.a1 import Config as ConfigBase
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.map_data = '''
    -- -- -- ++ ++ -- -- --
    -- -- -- -- -- -- -- --
    ++ ++ -- -- -- -- ++ ++
    -- -- -- ++ -- -- ++ ++
    -- -- -- ++ -- -- -- --
    -- -- -- -- -- -- -- ++
    -- -- -- ++ -- -- -- --
'''


class Config(ConfigBase):
    MAP_HAS_DYNAMIC_RED_BORDER = False


class Campaign(CampaignBase):
    MAP = MAP
