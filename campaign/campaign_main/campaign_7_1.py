from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger


MAP = CampaignMap()
MAP.map_data = '''
    -- -- -- -- -- -- ++ ++
    -- -- ++ ++ -- -- ++ ++
    -- -- ++ ++ -- -- -- --
'''
MAP.camera_data = ['D2', 'E2']


class Config:
    SUBMARINE = 0
    POOR_MAP_DATA = True
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40


class Campaign(CampaignBase):
    MAP = MAP
