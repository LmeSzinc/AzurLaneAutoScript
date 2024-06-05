from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('11-1')
MAP.shape = 'H6'
MAP.camera_data = ['D3', 'E4']
MAP.camera_data_spawn_point = ['D4']
MAP.map_data = """
    -- -- ME -- ME -- -- MB
    MB ME __ ME -- ++ ++ --
    ++ Me -- ++ ME MB ++ ME
    -- -- ++ ++ __ ME ME --
    SP -- -- -- Me ME -- ++
    ++ SP -- -- ++ -- MB ++
"""
MAP.weight_data = """
    90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 90
    90 90 90 90 90 90 90 90
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5},
    {'battle': 6, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
    = MAP.flatten()

road_main = RoadGrids([B2, B3, E5, F4, G4, H3])


class Config:
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 30
    EDGE_LINES_HOUGHLINES_THRESHOLD = 30
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.2


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):

        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True

        return self.battle_default()

    def battle_6(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                if self.clear_roadblocks([road_main]):
                    return True

        return self.fleet_boss.clear_boss()
