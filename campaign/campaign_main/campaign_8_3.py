from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_8_1 import Config as ConfigBase

MAP = CampaignMap('8-3')
MAP.shape = 'H6'
MAP.camera_data = ['D3', 'D4', 'E3', 'E4']
MAP.map_data = """
    MB -- ME ME ME ME -- MB
    -- ME MM ++ ++ __ ME --
    ME ++ ++ SP -- ME -- ME
    ME MA ++ -- SP ++ ME ME
    MM ME __ ME ++ ++ ME --
    MB -- ME ME ME ME -- MB
"""
MAP.weight_data = """
    50 50 40 90 90 30 50 50
    50 50 50 90 90 20 40 50
    40 90 90 10 10 10 20 20
    30 90 90 10 10 90 40 30
    20 20 20 10 90 90 40 50
    50 30 30 80 80 80 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2, 'mystery': 1},
    {'battle': 2, 'enemy': 2, 'mystery': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
    = MAP.flatten()

road_middle = RoadGrids([D5, F3])
step_on = SelectedGrids([D5, F3])
# There's one enemy spawn along with boss, so have to make sure there are multiple roads are cleared.
# Here use separate roads instead of RoadGrids.combine().
road_H1 = RoadGrids([F3, [F1, G2, H3]])
road_A6 = RoadGrids([D5, [B5, C6]])
road_A1_left = RoadGrids([A4, A3])
road_A1_upper = RoadGrids([F1, E1, D1, C1])
road_H6_bottom = RoadGrids([D6, E6, F6])
road_H6_right = RoadGrids([[H3, G4], [G4, H4], [H4, G5]])
road_MY = RoadGrids([[B2, C1]])


class Config(ConfigBase):
    pass


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.fleet_2_step_on(step_on, roadblocks=[road_middle]):
            return True

        self.clear_all_mystery()

        if self.clear_roadblocks([road_A6, road_H1, road_A1_left, road_A1_upper, road_H6_bottom, road_H6_right]):
            return True
        if self.clear_potential_roadblocks([road_A6, road_H1, road_A1_left, road_A1_upper, road_H6_bottom, road_H6_right]):
            return True
        if self.clear_roadblocks([road_MY]):
            return True
        if self.clear_first_roadblocks([road_A6, road_H1, road_A1_left, road_A1_upper, road_H6_bottom, road_H6_right]):
            return True

        return self.battle_default()

    def battle_4(self):
        return self.brute_clear_boss()
