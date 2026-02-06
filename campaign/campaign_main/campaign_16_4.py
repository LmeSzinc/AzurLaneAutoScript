from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

from .campaign_16_base_aircraft import CampaignBase
from .campaign_16_base_aircraft import Config as ConfigBase

MAP = CampaignMap('16-4')
MAP.shape = 'K8'
MAP.camera_data = ['C2', 'C6', 'F2', 'F6', 'H2', 'H6']
MAP.camera_data_spawn_point = ['C6']
MAP.camera_sight = (-2, -1, 3, 2)
MAP.map_data = """
    -- -- ++ -- -- -- ++ ME -- -- MB
    ME ++ ++ ++ -- -- ME ++ -- -- --
    -- -- ME -- -- ++ ++ ME -- -- --
    -- -- -- ME ++ -- ME -- ++ ++ --
    -- -- ME -- -- ME ++ -- ME ++ --
    -- __ -- ++ ++ -- ++ ME ME -- --
    SP -- -- ME -- -- ME ++ -- ++ ++
    SP -- -- -- ++ -- ++ ++ -- -- ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 40 50 50 50
    50 50 50 40 50 40 40 40 50 50 50
    50 50 50 40 40 40 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 5},
    {'battle': 1, 'enemy': 4},
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

road_main = RoadGrids([D4, F5, G4, H3])

class Config(ConfigBase):
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = True


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.clear_chosen_enemy(D4)
        return True

    def battle_1(self):
        if self.use_support_fleet:
            self.goto(D1)
            self.air_strike(B1)
        self.clear_chosen_enemy(F5)
        return True

    def battle_2(self):
        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()

    def battle_4(self):
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