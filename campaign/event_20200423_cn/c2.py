from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger
from campaign.event_20200423_cn.c1 import Config

MAP = CampaignMap()
MAP.map_data = '''
    -- -- -- -- -- -- --
    -- -- -- ++ ++ ++ --
    -- -- -- -- -- -- --
    -- -- ++ -- -- -- --
    -- -- -- -- -- -- --
    SP -- -- -- -- ++ --
    SP SP -- -- -- ++ --
'''


class Campaign(CampaignBase):
    MAP = MAP
