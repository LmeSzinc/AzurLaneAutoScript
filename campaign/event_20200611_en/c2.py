from campaign.event_20200611_en.c1 import Config
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.map_data = '''
    -- -- -- -- -- -- -- -- ++
    -- -- -- ++ ++ -- -- -- ++
    ++ -- -- -- -- -- -- -- --
    ++ -- ++ -- -- -- -- -- --
    -- -- -- -- ++ ++ -- -- --
    -- -- -- -- ++ ++ -- -- --
'''
MAP.camera_data = ['D1', 'D4', 'F2', 'F4']


class Campaign(CampaignBase):
    MAP = MAP
