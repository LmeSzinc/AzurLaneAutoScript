from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('SP')
MAP.shape = 'G10'
MAP.camera_data = ['D2', 'D6', 'D7']
MAP.camera_data_spawn_point = ['D7']
MAP.map_data = """
    -- -- ++ MB ++ -- --
    ++ ++ ++ -- ++ ++ ++
    ++ ME -- -- -- ME ++
    ++ -- -- ++ -- -- ++
    ++ ME -- -- -- ME ++
    ++ ++ ++ MS ++ ++ ++
    ++ -- -- -- -- -- ++
    MS -- -- __ -- -- MS
    ++ -- SP -- SP -- ++
    ++ ++ ++ -- ++ ++ ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'siren': 3},
    {'battle': 1},
    {'battle': 2},
    {'battle': 3, 'enemy': 4},
    {'battle': 4},
    {'battle': 5},
    {'battle': 6},
    {'battle': 7, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, \
A2, B2, C2, D2, E2, F2, G2, \
A3, B3, C3, D3, E3, F3, G3, \
A4, B4, C4, D4, E4, F4, G4, \
A5, B5, C5, D5, E5, F5, G5, \
A6, B6, C6, D6, E6, F6, G6, \
A7, B7, C7, D7, E7, F7, G7, \
A8, B8, C8, D8, E8, F8, G8, \
A9, B9, C9, D9, E9, F9, G9, \
A10, B10, C10, D10, E10, F10, G10, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['BBred', 'CV']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    # ===== End of generated config =====

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 24),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 24, 255),
        'prominence': 10,
        'distance': 50,
        # 'width': (0, 7),
        'wlen': 1000
    }
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    MAP_ENEMY_GENRE_DETECTION_SCALING = {
        'BBred': 1.111,
        'CV': 1.111,
    }
    MAP_SWIPE_MULTIPLY = 1.492
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.442


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True

        if self.clear_enemy(scale=(3,)):
            return True
        if self.clear_enemy(scale=(2,)):
            return True

        return self.battle_default()

    def battle_5(self):
        if self.clear_enemy(scale=(1,)):
            return True
        if self.clear_enemy(scale=(2,)):
            return True
        if self.clear_enemy(scale=(3,)):
            return True

        return self.battle_default()

    def battle_7(self):
        return self.fleet_boss.clear_boss()
