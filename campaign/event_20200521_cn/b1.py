from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.map_data = '''
    -- -- ++ ++ -- --
    -- -- ++ ++ -- --
    ++ -- -- -- -- --
    -- -- -- -- ++ --
    -- -- -- -- -- --
    ++ ++ -- -- -- --
    ++ -- -- -- ++ --
    -- -- -- -- -- --
    -- -- -- -- -- --
'''
MAP.camera_data = ['C3', 'C5', 'C7']


class Config:
    SUBMARINE = 0
    FLEET_BOSS = 1

    POOR_MAP_DATA = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_SIREN = True
    MAP_HAS_DYNAMIC_RED_BORDER = False
    MAP_HAS_MAP_STORY = True
    MAP_SIREN_TEMPLATE = ['Algerie', 'LaGalissonniere']
    MAP_SIREN_COUNT = 2

    TRUST_EDGE_LINES = False
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (100, 255 - 24),
        'width': 1,
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 24, 255),
        'prominence': 2,
        'distance': 50,
        'wlen': 1000
    }


class Campaign(CampaignBase):
    MAP = MAP
