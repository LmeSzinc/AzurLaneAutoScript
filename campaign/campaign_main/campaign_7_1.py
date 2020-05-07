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

    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 30
    EDGE_LINES_HOUGHLINES_THRESHOLD = 30
    MID_DIFF_RANGE_H = (140 - 3, 140 + 3)
    MID_DIFF_RANGE_V = (143 - 3, 143 + 3)

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (150, 255 - 24),
        'width': (0.5, 20),
        'prominence': 10,
        'distance': 35,
        'wlen': 100,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 24, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }


class Campaign(CampaignBase):
    MAP = MAP
