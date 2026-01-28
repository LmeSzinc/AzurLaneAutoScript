from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

from .campaign_16_base_aircraft import CampaignBase
from .campaign_16_base_aircraft import Config as ConfigBase

MAP = CampaignMap('16-3')
MAP.shape = 'K6'
MAP.camera_data = ['C2', 'C5', 'F2', 'F5', 'H2', 'H5']
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
    50 50 40 40 40 40 50 50 50 50 50
    50 50 50 50 50 40 40 40 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 6},
    {'battle': 2, 'enemy': 3},
    {'battle': 3, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, \
    = MAP.flatten()

road_main = RoadGrids([C3, D3, F3, G4, H4])


class Config(ConfigBase):
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = True


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.clear_chosen_enemy(C3)
        return True

    def battle_1(self):
        if self.use_support_fleet:
            self.air_strike(E3)
        self.clear_chosen_enemy(D3)
        return True

    def battle_2(self):
        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()

    def battle_3(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.clear_roadblocks([road_main])
            if self.use_support_fleet:
                # at this stage the most right zone should be accessible
                self.goto(K5)
                self.air_strike(J6)
            return self.fleet_boss.clear_boss()
        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()