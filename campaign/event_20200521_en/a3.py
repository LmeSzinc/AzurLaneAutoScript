from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('a3')
MAP.shape = 'K7'
# MAP.camera_data = ['D2', 'D5', 'F3', 'F5']
MAP.map_data = '''
    SP ++ ++ ++ ME -- -- -- ME -- MM
    -- -- -- -- -- -- ME -- -- -- --
    ME -- ++ ME -- -- -- -- ++ ++ --
    ME -- -- -- MS ++ __ -- MB ++ --
    -- -- ME -- -- -- -- -- -- -- --
    -- -- ++ ++ ME ME -- ME ++ ++ ++
    SP -- ++ MM ME -- -- -- -- ME MM
'''
# MAP.map_data = '''
#     SP ++ ++ ++ -- -- -- -- -- -- --
#     -- -- -- -- -- -- -- -- -- -- --
#     -- -- ++ -- -- -- -- -- ++ ++ --
#     -- -- -- -- -- ++ -- -- -- ++ --
#     -- -- -- -- -- -- -- -- -- -- --
#     -- -- ++ ++ -- -- -- -- ++ ++ ++
#     SP -- ++ ++ -- -- -- -- -- -- --
# '''

class Config:
    POOR_MAP_DATA = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_SIREN = True
    MAP_HAS_DYNAMIC_RED_BORDER = True
    MAP_SIREN_COUNT = 1
    MAP_GRID_CENTER_TOLERANCE = 0.3
    MAP_SIREN_TEMPLATE = ['1', '2', '3', 'DD']

    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 50
    MID_DIFF_RANGE_H = (45, 70)
    MID_DIFF_RANGE_V = (97 - 3, 97 + 3)
    TRUST_EDGE_LINES = True

    VANISH_POINT_RANGE = ((540, 740), (-4000, -2000))
    DISTANCE_POINT_X_RANGE = ((-2000, -1000),)
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 40),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
        'wlen': 100,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 40, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }


class Campaign(CampaignBase):
    MAP = MAP