from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .d1 import Config as ConfigBase

MAP = CampaignMap('D3')
MAP.shape = 'N10'
MAP.camera_data = ['F2', 'F6', 'F8', 'I2', 'I6', 'I8']
MAP.camera_data_spawn_point = ['F8', 'I8']
MAP.map_data = """
    -- -- -- -- -- ME -- -- ME -- -- -- -- ++
    -- -- -- ME -- -- MB MB -- -- ME -- -- --
    ++ -- ME -- Me ME -- -- ME Me -- ME -- --
    ++ -- -- ME -- -- __ __ -- -- ME -- -- --
    -- -- -- -- Me MS -- -- MS Me -- -- ++ ++
    -- ++ -- ME ++ ++ -- -- ++ ++ ME -- -- --
    -- ++ -- ME ++ ++ -- -- ++ ++ ME -- -- --
    -- -- -- -- Me MS -- -- MS Me -- -- ++ ++
    ++ -- -- -- -- -- -- -- -- -- -- -- ++ ++
    -- -- -- -- -- -- SP SP -- -- -- -- -- --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50 50 50 50
"""
MAP.wall_data = """
    ·   ·   ·   ·   · | ·   ·   ·   · | ·   ·   ·   ·   · ,
          +-----------+               +-----------+       ,
    ·   · | ·   ·   · | ·   ·   ·   · | ·   ·   · | ·   · ,
          |           |               |           |       ,
    ·   · | ·   ·   · | ·   ·   ·   · | ·   ·   · | ·   · ,
          +---+       +---+       +----+       +---+       ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |           ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |           ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |            ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |           ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |           ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              +-----------+       +-----------+           ,
    ·   ·   ·   ·   ·   · | ·   · | ·   ·   ·   ·   ·   · ,
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2, 'siren': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5, 'enemy': 1},
    {'battle': 6, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, L1, M1, N1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, L2, M2, N2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, L3, M3, N3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, L4, M4, N4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, L5, M5, N5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, L6, M6, N6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, K7, L7, M7, N7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, J8, K8, L8, M8, N8, \
A9, B9, C9, D9, E9, F9, G9, H9, I9, J9, K9, L9, M9, N9, \
A10, B10, C10, D10, E10, F10, G10, H10, I10, J10, K10, L10, M10, N10, \
    = MAP.flatten()


class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['Vauquelin', 'LaGalissonniere']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    # ===== End of generated config =====

    MAP_HAS_WALL = True


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(scale=(2,), genre=['light', 'main', 'enemy', 'carrier']):
            return True
        if self.clear_enemy(scale=(3,), genre=['light', 'main', 'enemy', 'carrier']):
            return True

        return self.battle_default()

    def battle_5(self):
        if self.clear_enemy(scale=(1,)):
            return True
        if self.clear_enemy(scale=(2,), genre=['light', 'main', 'enemy', 'carrier']):
            return True
        if self.clear_enemy(genre=['light', 'main']):
            return True

        return self.battle_default()

    def battle_6(self):
        return self.fleet_boss.brute_clear_boss()
