from campaign.event_20200423_cn.a1 import Config
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

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
