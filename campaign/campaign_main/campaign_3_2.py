from campaign.campaign_main.campaign_3_1 import Config
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'H4'
MAP.camera_data = ['E2']
MAP.camera_data_spawn_point = ['D1', 'D2']
MAP.map_data = """
    SP -- -- ME -- ME ME MB
    ++ ++ ME -- ME ++ ++ ++
    -- ++ -- ME -- MA ++ ++
    SP ME -- -- ME MM -- ++
"""
MAP.weight_data = """
    50 50 50 30 30 20 10 09
    50 50 40 40 30 20 10 10
    50 50 50 40 40 50 20 20
    50 50 50 50 35 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'mystery': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 2, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
    = MAP.flatten()


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.fleet_2_push_forward()

        if self.fleet_2_rescue(H1):
            return True

        self.clear_all_mystery()

        return self.battle_default()

    def battle_3(self):
        self.clear_all_mystery()

        if not self.check_accessibility(H1, fleet='boss'):
            return self.battle_default()

        return self.fleet_boss.clear_boss()
