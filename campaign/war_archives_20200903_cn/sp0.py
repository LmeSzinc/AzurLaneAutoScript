from .campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('SP0')
MAP.shape = 'J6'
MAP.camera_data = ['D2', 'D4', 'G2', 'G4']
MAP.camera_data_spawn_point = ['D2', 'D4']
MAP.map_data = """
    -- -- ++ ++ ++ ++ -- -- ++ ++
    -- ++ -- -- -- ++ -- -- -- ++
    SP -- -- -- -- -- ++ -- -- --
    SP -- -- -- -- -- -- -- -- MB
    -- -- -- -- ++ -- -- ++ -- --
    -- -- -- ++ ++ -- ++ ++ ++ --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50
"""
MAP.land_based_data = [['D6', 'up'], ['H5', 'up'], ['F2', 'down'], ['C1', 'down']]
MAP.spawn_data = [
    {'battle': 0, 'boss': 1},
    # {'battle': 1, 'enemy': 2},
    # {'battle': 2, 'enemy': 1},
    # {'battle': 3, 'enemy': 1, 'mystery': 1},
    # {'battle': 4, 'enemy': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, \
    = MAP.flatten()

mechanism = SelectedGrids([C6, E2, G5])


class Config:
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_LAND_BASED = True
    # ===== End of generated config =====

    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    MAP_IS_ONE_TIME_STAGE = True


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.clear_mechanism(mechanism)

        return self.clear_boss()
