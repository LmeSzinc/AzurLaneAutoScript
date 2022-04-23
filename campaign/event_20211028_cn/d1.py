from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('D1')
MAP.shape = 'F9'
MAP.camera_data = ['C2', 'C5', 'C7']
MAP.camera_data_spawn_point = ['C7']
MAP.map_data = """
    -- ME ++ ++ -- ME
    ME Me ++ ++ ME ME
    ++ -- MB MB -- --
    ME -- ME Me ++ Me
    ME MS __ __ Me ME
    ++ ++ MS -- MS --
    ++ MS -- ME ++ ME
    ME -- SP -- Me --
    ME -- SP SP -- ME
"""
MAP.weight_data = """
    50 50 50 50 50 50
    50 50 50 50 50 50
    50 50 50 50 50 50
    50 50 50 50 50 50
    50 50 50 50 50 50
    50 50 50 50 50 50
    50 50 50 50 50 50
    50 50 50 50 50 50
    50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5, 'enemy': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, \
A2, B2, C2, D2, E2, F2, \
A3, B3, C3, D3, E3, F3, \
A4, B4, C4, D4, E4, F4, \
A5, B5, C5, D5, E5, F5, \
A6, B6, C6, D6, E6, F6, \
A7, B7, C7, D7, E7, F7, \
A8, B8, C8, D8, E8, F8, \
A9, B9, C9, D9, E9, F9, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['LaGalissonniere', 'Algerie']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====

    DETECTION_BACKEND = 'perspective'
    TRUST_EDGE_LINES = False
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (100, 255 - 16),
        'width': 1,
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 16, 255),
        'prominence': 2,
        'distance': 50,
        'wlen': 1000
    }
    MAP_SWIPE_PREDICT_WITH_SEA_GRIDS = False
    MAP_SWIPE_MULTIPLY = 1.513
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.463


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_5(self):
        return self.fleet_boss.clear_boss()
