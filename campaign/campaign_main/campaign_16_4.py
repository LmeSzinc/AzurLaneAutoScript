from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

from .campaign_16_base_aircraft import CampaignBase
from .campaign_16_base_aircraft import Config as ConfigBase

MAP = CampaignMap('16-4')
MAP.shape = 'K8'
MAP.camera_data = ['C2', 'F5', 'F2', 'H2', 'H5']
MAP.camera_data_spawn_point = ['C6']
MAP.camera_sight = (-2, -1, 3, 2)
MAP.map_data = """
    -- -- ++ -- -- -- ++ ME -- -- MB
    ME ++ ++ ++ -- -- ME ++ -- -- --
    -- -- ME -- -- ++ ++ ME -- -- --
    -- -- -- ME ++ -- ME -- ++ ++ --
    -- -- -- ME -- ME ++ -- ME ++ --
    -- __ -- ++ ++ -- ++ ME ME -- --
    SP -- -- ME -- -- -- ++ -- ++ ++
    SP -- -- -- ++ -- ++ ++ -- -- ++
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
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 5},
    {'battle': 1, 'enemy': 3},
    {'battle': 2, 'enemy': 5},
    {'battle': 3},
    {'battle': 4},
    {'battle': 5},
    {'battle': 6},
    {'battle': 7},
    {'battle': 8, 'boss': 1},
]
MAP.spawn_data_loop = [
    {'battle': 0, 'enemy': 5},
    {'battle': 1, 'enemy': 3},
    {'battle': 2, 'enemy': 5},
    {'battle': 3},
    {'battle': 4, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, K7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, J8, K8, \
    = MAP.flatten()

road_main = RoadGrids([D5, F5, G4, H3])

class Config(ConfigBase):
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = True

    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom-left'
    MAP_SWIPE_MULTIPLY = (1.003, 1.022)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (0.970, 0.988)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (0.942, 0.959)


class Campaign(CampaignBase):
    MAP = MAP
    F5_is_moved = False
    use_single_fleet = False

    def map_init(self, map_):
        super().map_init(map_)
        self.F5_is_moved = False
        self.map_has_mob_move = self.use_support_fleet and self.map_is_clear_mode
        self.use_single_fleet = 'standby' in self.config.Fleet_FleetOrder

    def battle_0(self):
        if self.map_has_mob_move and not self.use_single_fleet:
            if self.mob_move(D7, D8):
                self.fleet_boss.goto(J1)
                self.fleet_ensure(index=3 - self.fleet_boss_index)
                if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
                    return True
                return self.battle_default()

            self.map_has_mob_move = False

        return self.clear_chosen_enemy(D5)

    def battle_1(self):
        if not self.map_has_mob_move:
            return self.clear_chosen_enemy(F5)

        if not self.use_single_fleet:
            if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
                return True
            return self.battle_default()

        grids = SelectedGrids([H6, I5])
        grid = grids.delete(grids.select(enemy_genre='Main')).first_or_none()
        if grid is not None and self.mob_move(F5, F6):
            self.F5_is_moved = True
            return self.clear_chosen_enemy(grid)

        self.F5_is_moved = False
        return self.clear_chosen_enemy(F5)

    def battle_2(self):
        if not self.map_has_mob_move or self.use_single_fleet:
            return self.clear_chosen_enemy(G4)

        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()

    def battle_3(self):
        if not self.map_has_mob_move:
            return self.clear_chosen_enemy(H3)

        if not self.use_single_fleet:
            if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
                return True
            return self.battle_default()

        if self.F5_is_moved:
            if I6.enemy_genre == "Main" and self.mob_move(I6, I7):
                return self.clear_any_enemy(genre=("Light",), strongest=True)
            return self.clear_chosen_enemy(I6)

        self.mob_move(H3, I3)
        self.mob_move(I3, I2)
        return self.clear_any_enemy(genre=("Light",), strongest=True)

    def battle_4(self):
        if self.map_is_clear_mode:
            return self.fleet_boss.clear_boss()

        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.clear_roadblocks([road_main])

            if self.use_support_fleet:
                # at this stage the most right zone should be accessible
                self.goto(J6)
                self.air_strike(I8)

            return self.fleet_boss.clear_boss()

        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()