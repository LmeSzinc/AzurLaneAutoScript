from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids

from .campaign_15_base import CampaignBase, W15GridInfo
from .campaign_15_base import Config as ConfigBase

MAP = CampaignMap('15-4')
MAP.grid_class = W15GridInfo
MAP.shape = 'K9'
MAP.camera_data = ['C2', 'C5', 'C7', 'F2', 'F5', 'F7', 'H2', 'H5', 'H7']
MAP.camera_data_spawn_point = ['H2']
MAP.camera_sight = (-2, -1, 3, 2)
MAP.map_data = """
    Me -- ME ME Me -- ME ++ ++ ME ME
    ME -- -- -- -- ME -- ++ ++ -- ME
    ++ -- -- MS -- -- ME SP SP ME Me
    ++ ME -- ++ ++ -- -- -- -- ME --
    -- Me ME MA ++ ME -- MS -- -- ME
    ME ME ME -- -- -- -- ++ ME -- Me
    ME -- __ -- ME ME -- ME ME -- ++
    -- -- ++ -- Me -- ME ME ME Me ME
    MB Me -- ME ME Me ++ ++ ++ -- Me
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 8},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1, 'siren': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5},
    {'battle': 6, 'siren': 1},
    {'battle': 7, 'enemy': 1},
    {'battle': 8, 'boss': 1},
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


class Config(ConfigBase):
    # ===== Start of generated config =====
    # MAP_SIREN_TEMPLATE = ['BOSS']
    # MOVABLE_ENEMY_TURN = (2,)
    # MAP_HAS_SIREN = True
    # MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = True
    # MAP_HAS_MYSTERY = True
    # ===== End of generated config =====

    MAP_SWIPE_MULTIPLY = (1.055, 1.075)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.020, 1.039)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (0.990, 1.008)


class Campaign(CampaignBase):
    MAP = MAP

    def battle_function(self):
        if not self.config.MAP_CLEAR_ALL_THIS_TIME:
            return super().battle_function()

        if self.battle_count in [3, 6] \
                or (self.battle_count in [0, 1] and not self.map_is_clear_mode):
            func = self.FUNCTION_NAME_BASE + str(self.battle_count)
            logger.info(f'Using function: {func}')
            func = self.__getattribute__(func)
            result = func()
            return result

        return super().battle_function()

    def battle_0(self):
        if not self.map_is_clear_mode and self.map_has_mob_move:
            self.mob_move(J8, K8)
            if K9.is_accessible:
                self.clear_chosen_enemy(K9)
                return True

        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_1(self):
        if not self.map_is_clear_mode:
            if A1.is_accessible:
                self.clear_chosen_enemy(A1)
                return True

        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_2(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_3(self):
        if not self.map_is_clear_mode:
            self.fleet_boss.clear_chosen_enemy(H5, expected='siren')
            self.fleet_1.switch_to()
            return True
        else:
            self.pick_up_ammo()
            self.clear_chosen_enemy(H5, expected='siren')
            return True

    def battle_4(self):
        self.pick_up_ammo()

        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_6(self):
        self.clear_chosen_enemy(D3, expected='siren')
        return True

    def battle_7(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_8(self):
        return self.fleet_boss.clear_boss()
