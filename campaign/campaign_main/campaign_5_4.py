from campaign.campaign_main.campaign_5_1 import Config as Config51
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'H5'
MAP.camera_data = ['D3', 'E3']
MAP.camera_data_spawn_point = ['D2', 'E3']
MAP.map_data = """
    ++ ++ ++ SP MB ME -- MB
    SP -- ME -- ME -- ME SP
    -- -- -- ++ ++ ME __ ME
    ME MB ME MA ++ -- ME --
    ++ ++ ME -- MB ME -- MB
"""
MAP.weight_data = """
    50 50 50 50 10 20 30 30
    50 50 10 10 10 10 30 30
    50 50 10 10 10 10 30 25
    50 10 10 10 10 10 30 30
    50 50 50 10 10 10 30 30
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 2},
    {'battle': 4, 'enemy': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
    = MAP.flatten()

road_center = RoadGrids([C2, [E2, F1], C4, F5, [F3, G2, H3], [F3, G4, H3]])
road_ring = RoadGrids([[E2, F1], [F1, G2, H3], [F5, G4, H3], [F3, G2, H3], [F3, G4, H3]])


class Config(Config51):
    MAP_MYSTERY_HAS_CARRIER = False
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_roadblocks([road_center]):
            return True
        if self.clear_potential_roadblocks([road_ring]):
            return True

        return self.battle_default()

    def battle_4(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                if self.clear_roadblocks([road_center]):
                    return True
                if self.clear_potential_roadblocks([road_ring]):
                    return True

        return self.fleet_boss.clear_boss()
