from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('10-4')
MAP.shape = 'I6'
MAP.camera_data = ['D2', 'F4']
MAP.camera_data_spawn_point = ['D4']
MAP.map_data = """
    MB ME ME -- ++ MB -- ++ ++
    ME ME ++ ME ++ -- Me -- ++
    -- __ ME Me ME ++ ME ME --
    ++ ++ ++ -- ME -- Me ++ ME
    SP -- -- Me -- ++ __ ME --
    SP -- -- -- Me ++ ME -- MB
"""
MAP.weight_data = """
    10 30 30 10 10 10 10 10 10
    5 30 10 30 10 10 5 10 10
    10 10 5 4 30 10 5 30 10
    10 10 10 10 10 10 5 10 30
    10 10 10 10 10 10 10 30 10
    10 10 10 10 30 10 5 10 10
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 4},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5},
    {'battle': 6, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, \
    = MAP.flatten()

step_on = SelectedGrids([E4, D3, G4, C3])
road_main = RoadGrids([D5, E4, D3, C3, A2, G4, H5, G3, G2])
roadblocks_d4 = RoadGrids([[D5, E6], E4, D3])


class Config:
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
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.fleet_2_step_on(step_on, roadblocks=[roadblocks_d4]):
            return True

        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True

        return self.battle_default()

    def battle_6(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                if self.clear_potential_roadblocks([road_main]):
                    return True

        return self.fleet_boss.clear_boss()
