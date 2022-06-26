from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_8_1 import Config as ConfigBase

MAP = CampaignMap('8-3')
MAP.shape = 'H5'
MAP.camera_data = ['D2', 'D3', 'E3']
MAP.camera_data_spawn_point = ['E3']
MAP.map_data = """
    MB ME -- ++ ++ ME -- MB
    ME ME ME -- ++ ME ME --
    -- ME -- ME ME -- ME ME
    ME ++ ++ -- ME ++ ++ ME
    MM ++ ++ ME ME SP -- SP
"""
MAP.weight_data = """
    50 35 20 90 90 40 50 50
    30 40 25 90 90 25 30 50
    20 20 20 10 10 20 20 35
    50 90 90 60 60 90 90 90
    90 90 90 70 80 90 90 90
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2, 'mystery': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
    = MAP.flatten()

road_A1 = RoadGrids([[A2, B1], [B1, B2, B3], [A2, B2, C2], [B3, C2], D3])
road_H1 = RoadGrids([[F1, G2, H3], [F1, G2, G3], [F2, G2, H3], [F2, G3], E3])
road_MY = RoadGrids([A4, [A2, B3]])
road_middle = RoadGrids([E5, [D5, E4], D3]) \
    .combine(RoadGrids([H4, H3, [F1, G2, G3], [F2, G3], E3]))
step_on = SelectedGrids([D3, E3])


class Config(ConfigBase):
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.fleet_2_step_on(step_on, roadblocks=[road_middle]):
            return True

        self.clear_all_mystery()

        if self.clear_roadblocks([road_A1, road_H1]):
            return True
        if self.mystery_count < 1 and self.clear_roadblocks([road_MY]):
            return True
        if self.clear_potential_roadblocks([road_A1, road_H1]):
            return True
        if self.clear_first_roadblocks([road_A1, road_H1]):
            return True

        return self.battle_default()

    def battle_4(self):
        return self.brute_clear_boss()
