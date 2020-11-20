from ..campaign_war_archives.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('SP.1')
MAP.shape = 'G3'
MAP.camera_data = ['D1']
MAP.camera_data_spawn_point = ['D1']
MAP.map_data = """
    ++ ++ ++ ++ -- -- MB
    -- Me -- -- ME ++ ++
    SP ++ ++ ++ -- ++ ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 1, 'mystery': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, \
A2, B2, C2, D2, E2, F2, G2, \
A3, B3, C3, D3, E3, F3, G3, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = True
    # ===== End of generated config =====


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        return self.battle_default()

    def battle_2(self):
        return self.clear_boss()
