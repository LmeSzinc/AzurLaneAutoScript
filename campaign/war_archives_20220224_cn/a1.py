from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from ..campaign_war_archives.campaign_base import CampaignBase

MAP = CampaignMap('A1')
MAP.shape = 'J6'
MAP.camera_data = ['D2', 'D4', 'G2', 'G4']
MAP.camera_data_spawn_point = ['D2', 'D4']
MAP.map_data = """
    ++ Me Me ++ ++ ++ ME -- ME ++
    -- -- -- ME -- -- -- -- -- --
    SP -- -- __ -- -- -- -- -- MB
    SP -- -- ME -- -- -- -- -- ME
    ++ -- -- -- ++ -- ME -- ME --
    ++ Me Me ++ ++ ME -- ++ ++ ++
"""
MAP.map_data_loop = """
    ++ Me Me ++ ++ ++ ME -- ME ++
    -- -- -- ME -- -- -- -- -- --
    SP -- -- __ -- MS -- MS -- MB
    SP -- -- ME -- -- -- -- -- ME
    ++ -- -- ME ++ -- ME -- ME --
    ++ Me Me ++ ++ ME -- ++ ++ ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1, 'boss': 1},
    {'battle': 4, 'enemy': 1},
]
MAP.spawn_data_loop = [
    {'battle': 0, 'enemy': 2, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1, 'boss': 1},
    {'battle': 4, 'enemy': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, \
    = MAP.flatten()

MAP.bouncing_enemy_data = [(C2, C3, C4), ]
MAP.fortress_data = [E3, (E2, F2, F3, E4, F4)]


class Config:
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====

    MAP_HAS_FORTRESS = True
    MAP_HAS_BOUNCING_ENEMY = True
    MAP_SWIPE_MULTIPLY = (1.111, 1.132)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.075, 1.094)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.043, 1.062)


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        if self.clear_bouncing_enemy():
            return True
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_3(self):
        return self.clear_boss()
