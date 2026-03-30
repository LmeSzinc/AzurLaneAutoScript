from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

from .campaign_16_base_aircraft import CampaignBase
from .campaign_16_base_aircraft import Config as ConfigBase

MAP = CampaignMap('16-3')
MAP.shape = 'K6'
MAP.camera_data = ['D3', 'E4', 'G2', 'H2']
MAP.camera_data_spawn_point = ['C5']
MAP.camera_sight = (-2, -1, 3, 2)
MAP.map_data = """
    -- -- ++ ++ ++ -- -- ME ++ -- MB
    -- ME -- ++ -- ME -- -- ++ -- --
    -- -- ME ME -- ME ++ ME ++ -- --
    -- -- -- ++ ++ __ ME ME -- -- --
    SP -- -- ++ -- ME ++ -- -- -- --
    SP -- -- ME ME -- ++ -- -- -- ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 6},
    {'battle': 2, 'enemy': 3},
    {'battle': 3},
    {'battle': 4},
    {'battle': 5},
    {'battle': 6},
    {'battle': 7, 'boss': 1},
]
MAP.spawn_data_loop = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 6},
    {'battle': 2, 'enemy': 3},
    {'battle': 3},
    {'battle': 4},
    {'battle': 5, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, \
    = MAP.flatten()

road_main = RoadGrids([G4, H4])


class Config(ConfigBase):
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = True

    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom-left'
    MAP_SWIPE_MULTIPLY = (1.180, 1.202)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.141, 1.162)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.108, 1.128)


class Campaign(CampaignBase):
    MAP = MAP
    use_single_fleet = False

    def map_init(self, map_):
        super().map_init(map_)
        self.map_has_mob_move = self.use_support_fleet and self.map_is_clear_mode
        self.use_single_fleet = 'standby' in self.config.Fleet_FleetOrder

    def battle_0(self):
        if self.map_has_mob_move:
            if self.mob_move(C3, C2):
                return self.clear_chosen_enemy(D6)
            self.map_has_mob_move = False

        return self.clear_chosen_enemy(C3)

    def battle_1(self):
        if self.map_has_mob_move:
            self.mob_move(E6, E5)
            if not self.use_single_fleet:
                self.fleet_boss.goto(F4)
                self.fleet_ensure(index=3 - self.fleet_boss_index)
            return self.clear_chosen_enemy(G4)

        if self.use_support_fleet and not self.map_is_clear_mode:
            self.goto(C3)
            self.air_strike(E3)
        return self.clear_chosen_enemy(D3)

    def battle_2(self):
        return self.clear_chosen_enemy(F3)

    def battle_3(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.clear_roadblocks([road_main])
            if self.use_support_fleet and not self.map_is_clear_mode:
                # at this stage the most right zone should be accessible
                self.goto(K5)
                self.air_strike(J6)
            return self.fleet_boss.clear_boss()
        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_any_enemy(genre=("Light",), strongest=True):
            return True
        return self.battle_default()