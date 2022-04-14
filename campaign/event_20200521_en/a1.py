from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('a1')
MAP.shape = 'I5'
MAP.map_data = '''
    SP -- ++ ME -- ME ++ -- --
    -- ME -- -- ME -- ME ++ ME
    -- -- MS -- -- MS __ -- --
    -- ME -- -- ++ ME -- ME --
    SP -- -- ME ++ -- ME -- MB
'''
MAP.camera_data = ['D1', 'D3', 'F1', 'F3']

class Config:
    POOR_MAP_DATA = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_SIREN = True
    MAP_HAS_DYNAMIC_RED_BORDER = True
    MAP_SIREN_COUNT = 1

    TRUST_EDGE_LINES = True

    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5
    MID_DIFF_RANGE_H = (140 - 3, 140 + 3)
    MID_DIFF_RANGE_V = (143 - 3, 143 + 3)

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

    def handle_boss_appear_refocus(self, preset=(-3, -2)):
        return super().handle_boss_appear_refocus(preset)
