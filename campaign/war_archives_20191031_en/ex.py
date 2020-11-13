from ..campaign_war_archives.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('EX')
MAP.shape = 'F5'
MAP.camera_data = ['C2', 'C3']
MAP.camera_data_spawn_point = ['C3']
MAP.map_data = """
    ++ ++ ++ ++ ++ ++
    ++ -- -- -- -- ++
    ++ SP -- -- MB ++
    ++ -- -- -- -- ++
    ++ ++ ++ ++ ++ ++
"""
MAP.weight_data = """
    50 50 50 50 50 50
    50 50 50 50 50 50
    50 50 50 50 50 50
    50 50 50 50 50 50
    50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 1, 'boss': 1},
    {'battle': 1, 'enemy': 1},
]
A1, B1, C1, D1, E1, F1, \
A2, B2, C2, D2, E2, F2, \
A3, B3, C3, D3, E3, F3, \
A4, B4, C4, D4, E4, F4, \
A5, B5, C5, D5, E5, F5, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = False
    # ===== End of generated config =====


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        return self.battle_default()

    def battle_0(self):
        return self.clear_boss()
