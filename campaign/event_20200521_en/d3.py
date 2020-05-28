from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger


MAP = CampaignMap('d3')
MAP.shape = 'I9'
MAP.map_data = '''
    SP -- ++ ++ -- MS -- ME --
    -- ME ++ ++ -- ME -- -- --
    -- -- -- -- -- -- ME ME --
    ME -- ME ME -- ME ++ ++ ++
    -- -- ++ __ -- -- -- MB ++
    -- ME ++ -- -- ME ++ ++ ++
    -- -- MS -- ++ ME -- ME --
    SP -- -- -- ++ -- -- ME --
    SP -- MS -- -- ME -- -- -- 
'''


class Config:
    SUBMARINE = 1
    FLEET_BOSS = 2

    POOR_MAP_DATA = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_SIREN = True
    MAP_HAS_DYNAMIC_RED_BORDER = True
    MAP_SIREN_COUNT = 3

    TRUST_EDGE_LINES = True

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 40),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 40, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }


class Campaign(CampaignBase):
    MAP = MAP

