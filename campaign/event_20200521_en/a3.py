from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('')
# MAP.shape = 'K7'
# MAP.camera_data = ['D2', 'D5', 'F3', 'F5']
# MAP.map_data = '''
#     SP ++ ++ ++ ME -- -- -- ME -- MM
#     -- -- -- -- -- -- ME -- -- -- --
#     ME -- ++ ME -- -- -- -- ++ ++ --
#     ME -- -- -- MS ++ __ -- MB ++ --
#     -- -- ME -- -- -- -- -- -- -- --
#     -- -- ++ ++ ME ME -- ME ++ ++ ++
#     SP -- ++ MM ME -- -- -- -- ME MM
# '''
MAP.map_data = '''
    SP ++ ++ ++ -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- --
    -- -- ++ -- -- -- -- -- ++ ++ --
    -- -- -- -- -- ++ -- -- -- ++ --
    -- -- -- -- -- -- -- -- -- -- --
    -- -- ++ ++ -- -- -- -- ++ ++ ++
    SP -- ++ ++ -- -- -- -- -- -- --
'''

class Config:
    SUBMARINE = 0
    FLEET_BOSS = 0

    POOR_MAP_DATA = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_SIREN = True
    MAP_HAS_DYNAMIC_RED_BORDER = False
    MAP_HAS_MAP_STORY = True
    MAP_SIREN_COUNT = 0

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