from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from ..campaign_war_archives.campaign_base import CampaignBase
from .a1 import EventGrid

MAP = CampaignMap('C1')
MAP.shape = 'H5'
MAP.camera_data = ['D2', 'D3', 'E2', 'E3']
MAP.camera_data_spawn_point = ['D3', 'C1']
MAP.map_data = """
    SP -- -- ++ ++ ++ ++ ++
    -- ++ ME Me ME -- Me ++
    SP -- Me -- ME ++ ME MB
    -- -- ++ ME ME ++ ME MB
    SP -- ++ -- Me -- ME MB
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50
    50 50 30 30 30 50 20 50
    50 50 10 50 50 50 20 10
    50 50 50 10 50 50 50 10
    50 50 50 50 10 50 10 10
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 4},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
    = MAP.flatten()

class Config:
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = True
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        if self.fleet_2_push_forward():
            return True

        return self.battle_default()

    def battle_5(self):
        return self.fleet_boss.clear_boss()
