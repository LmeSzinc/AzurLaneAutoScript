from .campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('SP')
MAP.shape = 'I9'
MAP.camera_data = ['C5', 'F5']
MAP.camera_data_spawn_point = ['E7']
MAP.camera_sight = (-2, -1, 3, 2)
MAP.map_data = """
    -- ++ ++ -- -- -- ++ ++ --
    -- ++ ++ -- MB -- ++ ++ --
    ++ ++ ++ ++ -- ++ ++ ++ ++
    -- ME ++ -- -- -- ++ ME --
    ME -- -- -- __ -- -- -- ME
    -- ME ++ -- -- -- ++ ME --
    ++ ++ ++ ++ -- ++ ++ ++ ++
    -- ++ ++ -- -- -- ++ ++ --
    -- ++ ++ SP -- SP ++ ++ --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 6, 'siren': 4},
    {'battle': 1},
    {'battle': 2},
    {'battle': 3},
    {'battle': 4},
    {'battle': 5},
    {'battle': 6},
    {'battle': 7, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, \
A9, B9, C9, D9, E9, F9, G9, H9, I9, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    # ===== End of generated config =====

    MAP_HAS_SIREN = True
    MAP_HAS_CLEAR_PERCENTAGE = False
    MAP_IS_ONE_TIME_STAGE = True
    HOMO_STORAGE = ((9, 6), [(165.083, 80.309), (1168.09, 80.309), (21.023, 612.379), (1325.484, 612.379)])

    MAP_SWIPE_MULTIPLY = (1.009, 1.028)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (0.976, 0.994)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (0.948, 0.965)
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    MAP_WALK_USE_CURRENT_FLEET = True


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def map_data_init(self, map_):
        super().map_data_init(map_)
        D4.is_siren = True
        D6.is_siren = True
        F4.is_siren = True
        F6.is_siren = True

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=2):
            return True

        return self.battle_default()

    def battle_5(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_7(self):
        return self.fleet_boss.clear_boss()

    def is_event_animation(self):
        # Red-black banner with white bottom border
        if self.image_color_count((1193, 322, 1273, 329), color=(255, 255, 255), count=500):
            logger.info('Live start!')
            return True

        return False