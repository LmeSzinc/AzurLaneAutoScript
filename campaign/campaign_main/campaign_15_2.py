from module.base.decorator import Config
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids

from .campaign_15_base import CampaignBase
from .campaign_15_base import Config as ConfigBase

MAP = CampaignMap('15-2')
MAP.shape = 'I8'
MAP.camera_data = ['D2', 'D6', 'F2', 'F6']
MAP.camera_data_spawn_point = ['F2']
MAP.map_data = """
    ME -- ME ME Me -- ++ ++ ++
    ME -- -- ++ ME ME ME SP SP
    -- ME ME Me -- -- -- -- --
    -- -- -- -- -- ME ME Me --
    ME -- ++ ME Me -- ME ME --
    Me -- ME __ ME ++ ++ ++ --
    ++ MB -- ME ME ++ -- MB --
    ++ MB ME -- ME -- -- -- ME
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 6},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1},
    {'battle': 3},
    {'battle': 4},
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

# W15 has special enemy spawn mechanism
# After entering map, additional enemies spawn on these nodes:
# ['F8', 'I6'] must spawns an enemy.
# Additionally, 'G7' spawns a special carrier 
# which allows mob air reinforcement.
OVERRIDE = CampaignMap('15-2')
OVERRIDE.map_data = """
    ME -- ME ME ME -- -- -- --
    ME -- -- -- ME ME ME -- --
    -- ME ME ME -- -- -- -- --
    -- -- -- -- -- ME ME ME --
    ME -- -- ME ME -- ME ME --
    ME -- ME -- ME -- -- -- ME
    -- -- -- ME ME -- ME -- --
    -- -- ME -- ME ME -- -- ME
"""


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
    
    def map_data_init(self, map_):
        super().map_data_init(map_)
        for override_grid in OVERRIDE:
            # Set may_enemy, but keep may_ambush
            self.map[override_grid.location].may_enemy = override_grid.may_enemy

    @Config.when(Campaign_UseClearMode=False)
    def battle_0(self):
        self.mob_move(I6, I7)
        self.mob_move(I7, H7)
        self.full_scan_movable()
        self.goto(G7)
        return True

    @Config.when(Campaign_UseClearMode=True)
    def battle_0(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True

        return self.battle_default()

    def battle_1(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True
        
        return self.battle_default()

    def battle_5(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_6(self):
        return self.fleet_boss.clear_boss()
