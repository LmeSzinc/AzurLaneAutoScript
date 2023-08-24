from campaign.campaign_main.campaign_2_1 import Config as ConfigBase
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'G4'
MAP.camera_data = ['D2']
MAP.camera_data_spawn_point = ['D2']
MAP.map_data = """
    -- ++ ++ ++ ME ME MB
    SP -- ME -- -- ME --
    -- -- ME -- ME ++ ++
    -- ME -- SP -- MA ++
"""
MAP.weight_data = """
    20 20 20 20 12 11 10
    20 20 20 20 10 10 10
    20 20 20 20 30 20 20
    20 20 20 20 20 20 20
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 2, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, \
A2, B2, C2, D2, E2, F2, G2, \
A3, B3, C3, D3, E3, F3, G3, \
A4, B4, C4, D4, E4, F4, G4, \
    = MAP.flatten()

road_main = RoadGrids([[F2, F1], [F2, E1], [C2, C3, B4]])

class Config(ConfigBase):
    # Don't know why 2-4 is slimmer
    # 2-1 is /_\ and 2-4 is like |_|
    MID_DIFF_RANGE_H = (121 - 3, 121 + 3)
    MID_DIFF_RANGE_V = (121 - 3, 121 + 3)


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        # Even adding these precautions, there is still possibility that F2 and E1 spawns at the same time.
        # However adding these can reduce the other possibilities.
        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True

        return self.battle_default()

    def battle_3(self):
        if not self.check_accessibility(G1, fleet='boss'):
            if self.clear_roadblocks([road_main]):
                return True
            return self.battle_default()

        return self.fleet_boss.clear_boss()
