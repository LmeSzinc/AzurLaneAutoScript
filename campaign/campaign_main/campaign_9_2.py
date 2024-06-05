from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('9-2')
MAP.shape = 'I5'
MAP.camera_data = ['D3', 'E3']
MAP.camera_data_spawn_point = ['D3']
MAP.map_data = """
    ++ ++ ME -- MB ME -- Me --
    MM ++ ME ME MB ME ++ ME --
    ME -- Me ++ ++ ++ ++ Me ++
    -- ++ -- -- ++ SP -- ME --
    -- ME -- SP ++ SP -- -- --
"""
MAP.weight_data = """
    10 10 30 10 10 10 10 10 10
    10 10 20 30 10 30 10 10 10
    30 10 20 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 30 10 10 10 10 10 10 10
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2, 'mystery': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
    = MAP.flatten()

road_main = RoadGrids([C3, C2, [C1, D2], F1, H1, H2, H3, H4])


class Config:
    SUBMARINE = 0
    MAP_HAS_MYSTERY = True
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (150, 255 - 24),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 24, 255),
        'prominence': 10,
        'distance': 50,
        'width': (0, 10),
        'wlen': 1000,
    }
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.fleet_at(D5, fleet=2):
            self.map.weight_data = """
                10 10 30 10 10 20 30 40 10
                10 10 10 10 10 30 10 50 10
                30 10 10 10 10 10 10 60 10
                10 10 10 10 10 10 10 70 10
                10 30 10 10 10 10 10 10 10
            """
        if self.fleet_at(F4, fleet=2):
            self.map.weight_data = """
                10 10 30 10 10 10 10 10 10
                10 10 20 30 10 30 10 10 10
                30 10 20 10 10 10 10 10 10
                10 10 10 10 10 10 10 10 10
                10 30 10 10 10 10 10 10 10
            """
        if self.fleet_at(F5, fleet=2):
            self.map.weight_data = """
                10 10 30 10 10 10 10 10 10
                10 10 20 30 10 30 10 10 10
                30 10 20 10 10 10 10 10 10
                10 10 10 10 10 10 10 10 10
                10 30 10 10 10 10 10 10 10
            """
        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True

        return self.battle_default()

    def battle_5(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                if self.clear_roadblocks([road_main]):
                    return True

        return self.fleet_boss.clear_boss()
