from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_8_1 import Config as ConfigBase

MAP = CampaignMap('8-4')
MAP.shape = 'H7'
MAP.camera_data = ['D3', 'E3', 'E5']
MAP.camera_data_spawn_point = ['C1']
MAP.map_data = """
    ++ SP -- -- ME -- ME --
    SP -- -- ME -- ++ ++ --
    -- -- ME ++ ++ MM ME ME
    ++ ++ -- ++ ++ ME ME --
    MA ++ ME -- ME __ ME ++
    ME ME __ ME ++ ++ -- ME
    -- ME ME MM ME -- ME MB
"""
MAP.weight_data = """
    50 50 50 90 90 90 90 90
    50 50 50 90 90 90 90 90
    50 50 45 90 90 50 50 90
    90 90 40 90 90 30 31 90
    50 90 30 30 20 14 12 90
    30 27 35 25 90 90 20 10
    30 28 26 20 13 15 10 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 2, 'mystery': 1},
    {'battle': 3, 'enemy': 1, 'mystery': 1},
    {'battle': 4, 'enemy': 2, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
A7, B7, C7, D7, E7, F7, G7, H7, \
    = MAP.flatten()

road_D7 = RoadGrids([G7, E7]).combine(RoadGrids([G5, E5, [C5, D6], [D6, C7]]))
road_F3 = RoadGrids([G5, [F4, G4], [F4, G3]])
road_main = RoadGrids([[G7, H6]])


class Config(ConfigBase):
    pass


class Campaign(CampaignBase):
    MAP = MAP
    # Need to increase this threshold a little bit, because of mis-detection on dark background
    MAP_AMBUSH_OVERLAY_TRANSPARENCY_THRESHOLD = 0.45
    MAP_AIR_RAID_OVERLAY_TRANSPARENCY_THRESHOLD = 0.45  # Usually (0.50, 0.53)

    def battle_0(self):
        self.fleet_2_push_forward()

        self.clear_all_mystery()

        if self.clear_roadblocks([road_D7, road_F3, road_main]):
            return True
        if self.clear_potential_roadblocks([road_D7, road_F3, road_main]):
            return True
        if self.clear_first_roadblocks([road_D7, road_F3, road_main]):
            return True

        return self.battle_default()

    def battle_4(self):
        self.clear_all_mystery()

        return self.brute_clear_boss()
