import copy

# Do not remove the Config import. It's inherited from 15-4 and needs to be exported.
from .campaign_15_4 import Config # noqa # pylint: disable=unused-import
from .campaign_15_4 import MAP as MAP_15_4, Campaign as Campaign_15_4 

MAP = copy.copy(MAP_15_4)
MAP.name = '15-4-121'

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

class Campaign(Campaign_15_4):
    MAP = MAP

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
        self.pick_up_ammo()
        self.clear_chosen_enemy(H5, expected='siren')
        return True

    def battle_4(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_6(self):
        self.fleet_boss.clear_chosen_enemy(D3, expected='siren')
        self.fleet_1.switch_to()
        return True

    def battle_7(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_8(self):
        return self.clear_boss()
