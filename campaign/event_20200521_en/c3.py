from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('c3')
MAP.shape = 'K7'
MAP.camera_data = ['F2', 'F4', 'F6']
MAP.map_data = '''
    SP ++ ++ ++ ME -- -- MS ME -- MM
    -- -- -- -- -- -- ME -- -- -- --
    ME -- ++ ME -- -- -- -- ++ ++ --
    ME -- -- -- MS ++ __ -- MB ++ --
    -- -- ME -- -- -- -- -- -- -- --
    -- -- ++ ++ ME ME -- ME ++ ++ ++
    SP -- ++ ++ ME -- -- -- -- ME MM
'''

# A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, \
# A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, \
# A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, \
# A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, \
# A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, \
# A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, \
# A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, K7, \
#     = MAP.flatten()

class Config:
    POOR_MAP_DATA = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_SIREN = True
    # MAP_HAS_DYNAMIC_RED_BORDER = False
    MAP_SIREN_COUNT = 2
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

