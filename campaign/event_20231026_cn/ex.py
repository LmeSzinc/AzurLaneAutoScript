from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('EX')
MAP.shape = 'E7'
MAP.camera_data = ['C4']
MAP.camera_data_spawn_point = ['C4']
MAP.map_data = """
    ++ ++ ++ ++ ++
    -- ++ ++ ++ --
    -- ++ ++ ++ --
    ++ ++ MB ++ ++
    ++ -- -- -- ++
    -- -- SP -- --
    -- ++ ++ ++ --
"""
MAP.weight_data = """
    50 50 50 50 50
    50 50 50 50 50
    50 50 50 50 50
    50 50 50 50 50
    50 50 50 50 50
    50 50 50 50 50
    50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'boss': 1},
]
A1, B1, C1, D1, E1, \
A2, B2, C2, D2, E2, \
A3, B3, C3, D3, E3, \
A4, B4, C4, D4, E4, \
A5, B5, C5, D5, E5, \
A6, B6, C6, D6, E6, \
A7, B7, C7, D7, E7, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    # ===== End of generated config =====


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_0(self):
        return self.clear_boss()
