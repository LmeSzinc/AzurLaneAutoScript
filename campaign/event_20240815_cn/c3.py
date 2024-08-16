from .campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger
from .c1 import Config as ConfigBase

MAP = CampaignMap('C3')
MAP.shape = 'O5'
MAP.camera_data = ['F2', 'F3', 'J2', 'J3']
MAP.camera_data_spawn_point = ['J2']
MAP.map_data = """
    -- -- ++ ++ ++ ME -- ++ ++ SP -- SP -- ++ --
    -- -- -- ++ ME -- ME ++ ++ -- -- -- -- ++ ++
    -- -- MB -- -- __ -- ME -- -- MS -- MS ++ ++
    -- -- -- ++ ME -- -- -- -- Me -- ++ -- -- --
    -- -- ++ ++ ++ ME ME ++ Me -- Me ++ -- -- --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, L1, M1, N1, O1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, L2, M2, N2, O2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, L3, M3, N3, O3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, L4, M4, N4, O4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, L5, M5, N5, O5, \
    = MAP.flatten()


class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = []
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====

    MAP_SWIPE_MULTIPLY = (1.240, 1.263)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.199, 1.221)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.164, 1.185)


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
