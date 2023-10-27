from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_14_base import CampaignBase
from .campaign_14_base import Config as ConfigBase

MAP = CampaignMap('14-4')
MAP.shape = 'K9'
MAP.camera_data = ['D2', 'D5', 'D7', 'H2', 'H5', 'H7']
MAP.camera_data_spawn_point = ['H2']
MAP.map_covered = ['A4']
MAP.map_data = """
    ME -- ++ ++ -- ME ME ME ++ ++ ++
    -- ME ME ME ME ME ME -- SP SP --
    MB -- __ -- -- -- -- -- ME -- --
    MB ME -- Me Me -- Me ++ ++ -- ME
    MM -- Me ME -- Me -- MA ++ -- ME
    ++ ME ME -- ++ -- ME -- ME -- --
    ++ -- ME Me Me ME -- -- -- -- ++
    -- -- -- -- -- __ -- ME ME -- ME
    -- -- ++ MB MB ++ ++ MM ME ME ME
"""
MAP.weight_data = """
    40 40 40 40 50 50 50 50 50 50 50
    40 40 40 40 50 50 50 50 50 50 50
    40 40 40 40 50 50 50 50 50 50 50
    40 40 40 40 50 50 50 50 50 50 50
    40 40 40 40 50 50 50 50 50 50 50
    40 40 40 40 50 50 50 50 50 50 50
    40 40 40 40 50 50 50 50 50 50 50
    50 10 50 50 50 50 50 40 40 50 50
    50 50 50 50 50 50 50 50 50 40 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 3},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 2},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'enemy': 1},
    {'battle': 6},
    {'battle': 7, 'boss': 1},
]
MAP.spawn_data_loop = [
    {'battle': 0, 'enemy': 2},
    {'battle': 1, 'enemy': 3},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 2},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'enemy': 1},
    {'battle': 6},
    {'battle': 7, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, K7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, J8, K8, \
A9, B9, C9, D9, E9, F9, G9, H9, I9, J9, K9, \
    = MAP.flatten()

# 14-4 has special enemy spawn mechanism
# After entering map or each battle, enemies spawn on these nodes:
# ['C2', 'D3', 'D4', 'H8', 'I7'], and 'B8' must spawns an enemy
# ['A1', 'B2', 'B6', 'C7']
# ['F5', 'G4', 'G6', 'I8', 'J9']
# ['F2', 'G1', 'H2', 'K4', 'K5']
# ['C5', 'C6', 'D5']
# ['E8', 'G8']
OVERRIDE = CampaignMap('14-4')
OVERRIDE.map_data = """
    ME -- -- -- -- -- ME -- -- -- --
    -- ME ME -- -- ME -- ME -- -- --
    -- -- -- ME -- -- -- -- -- -- --
    -- -- -- ME -- -- ME -- -- -- ME
    -- -- ME ME -- ME -- -- -- -- ME
    -- ME ME -- -- -- ME -- -- -- --
    -- -- ME -- -- -- -- -- ME -- --
    -- ME -- -- ME -- ME ME ME -- --
    -- -- -- -- -- -- -- -- -- ME --
"""
road_A8 = RoadGrids([B8])
road_H9 = RoadGrids([[H8, I8, J9], ])


class Config(ConfigBase):
    # ===== Start of generated config =====
    # MAP_SIREN_TEMPLATE = ['0']
    # MOVABLE_ENEMY_TURN = (2,)
    # MAP_HAS_SIREN = True
    # MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = True
    # MAP_HAS_MYSTERY = True
    # ===== End of generated config =====

    MAP_WALK_USE_CURRENT_FLEET = True


class Campaign(CampaignBase):
    MAP = MAP

    def map_data_init(self, map_):
        super().map_data_init(map_)
        for override_grid in OVERRIDE:
            # Set may_enemy, but keep may_ambush
            self.map[override_grid.location].may_enemy = override_grid.may_enemy

    def battle_0(self):
        self.pick_up_light_house(A9)

        if self.clear_roadblocks([road_A8, road_H9], weakest=False):
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True

        return self.battle_default()

    def battle_3(self):
        self.pick_up_light_house(A9)
        self.pick_up_ammo()
        self.pick_up_flare(H9)

        if self.clear_roadblocks([road_A8, road_H9], weakest=False):
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True

        return self.battle_default()

    def battle_6(self):
        self.pick_up_light_house(A9)
        self.pick_up_ammo()
        self.pick_up_flare(H9)

        if self.clear_roadblocks([road_A8, road_H9], weakest=False):
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_7(self):
        self.fleet_boss.pick_up_flare(A5)

        return self.fleet_boss.clear_boss()
