from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_14_base import CampaignBase
from .campaign_14_base import Config as ConfigBase

MAP = CampaignMap('14-2')
MAP.shape = 'I8'
MAP.camera_data = ['D2', 'D6', 'F2', 'F6']
MAP.camera_data_spawn_point = ['F2']
MAP.map_data = """
    MB MB ++ -- ME -- ME ++ ++
    -- ME ++ ME -- Me -- SP SP
    -- -- Me Me Me -- -- ME ME
    ME __ -- Me -- ME -- -- ME
    MM ME -- -- Me -- -- ME ++
    ++ ++ ++ -- ++ -- ME ME ME
    Me MB ME __ -- -- Me MM ME
    ME -- -- -- ME ME ++ ++ ME
"""
MAP.weight_data = """
    50 50 50 60 60 60 50 50 50
    50 50 50 60 60 50 50 50 50
    50 50 50 60 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 60 70
    50 50 50 50 50 50 50 60 80
    50 50 50 50 50 50 50 50 90
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5},
    {'battle': 6, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, \
    = MAP.flatten()
road_H7 = RoadGrids([[G6, G7, H6], [G6, G7, H7]])
road_A5 = RoadGrids([[A4, B5]])


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


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        # 14-2 do not have light house

        if not self.picked_flare and H7.is_accessible and A5.is_accessible:
            self.fleet_boss.pick_up_flare(H7)
            self.fleet_boss.pick_up_flare(A5)
            self.fleet_boss.goto(D6)
            self.fleet_1.switch_to()

        if self.clear_roadblocks([road_A5, road_H7], weakest=True):
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True

        return self.battle_default()

    def battle_5(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_6(self):
        return self.fleet_boss.clear_boss()
