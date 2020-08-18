from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger


MAP = CampaignMap()
MAP.map_data = '''
    -- -- -- -- -- -- -- --
    -- -- ++ -- -- -- -- --
    -- -- -- -- -- ++ ++ ++
    -- -- -- -- -- -- ++ ++
    -- ++ ++ ++ -- -- ++ --
    -- -- -- ++ -- -- -- --
'''


class Config:
    SUBMARINE = 0
    POOR_MAP_DATA = True


class Campaign(CampaignBase):
    MAP = MAP
