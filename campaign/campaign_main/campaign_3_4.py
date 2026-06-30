from campaign.campaign_main.campaign_3_1 import Config as Config31
from .campaign_3_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'H4'
MAP.camera_data = ['E2']
MAP.camera_data_spawn_point = ['D1', 'D2']
# WIKI的图是错的: https://wiki.biligame.com/blhx/3-4
# A3有岛, 假图害人
MAP.map_data = """
    SP -- -- ME -- ++ ++ ++
    SP ME -- ME -- MA ++ ++
    ++ -- ME __ ME ME -- MB
    SP ME -- ME -- -- ME MB
"""
MAP.weight_data = """
    40 40 40 40 40 40 40 40
    40 40 40 30 30 30 30 30
    40 40 30 30 20 10 10 09
    40 40 30 20 20 10 10 09
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
    = MAP.flatten()


class Config(Config31):
    MAP_MYSTERY_HAS_CARRIER = False

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (120, 255 - 75),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 40, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.fleet_2_push_forward()

        if self.fleet_2_rescue(H3):
            return True

        return self.battle_default()

    def battle_3(self):
        if not self.check_accessibility(H3, fleet='boss'):
            return self.battle_default()

        return self.fleet_boss.clear_boss()

    # def handle_boss_appear_refocus(self):
    #     for data in self.map.spawn_data:
    #         if data.get('battle') == self.battle_count and data.get('boss', 0):
    #             self.map_swipe((-3, -1))
    #
    #     return super().handle_boss_appear_refocus()
