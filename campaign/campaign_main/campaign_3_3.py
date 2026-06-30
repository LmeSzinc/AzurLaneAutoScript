from campaign.campaign_main.campaign_3_1 import Config as ConfigBase
from .campaign_3_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'F5'
MAP.camera_data = ['D3']
MAP.camera_data_spawn_point = ['D3']
MAP.map_data = """
    ++ ++ ME MM ++ ++
    ++ ++ -- ME -- SP
    -- ++ ME -- ME --
    MB ME -- ME -- --
    -- ME ME SP ME SP
"""
MAP.weight_data = """
    50 50 30 30 50 50
    50 50 30 30 50 50
    50 50 20 30 50 50
    09 10 11 20 50 50
    10 10 11 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'mystery': 1},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, \
A2, B2, C2, D2, E2, F2, \
A3, B3, C3, D3, E3, F3, \
A4, B4, C4, D4, E4, F4, \
A5, B5, C5, D5, E5, F5, \
    = MAP.flatten()


class Config(ConfigBase):
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.fleet_2_push_forward()

        if self.fleet_2_rescue(A4):
            return True

        self.clear_all_mystery()

        return self.battle_default()

    def battle_3(self):
        self.clear_all_mystery()

        if not self.check_accessibility(A4, fleet='boss'):
            return self.battle_default()

        return self.fleet_boss.clear_boss()
