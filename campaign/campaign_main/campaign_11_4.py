from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('11-4')
MAP.shape = 'J8'
MAP.camera_data = ['D2', 'D6', 'G2', 'G6']
MAP.camera_data_spawn_point = ['D2', 'G2']
MAP.map_data = """
    MB MB ++ -- -- -- ++ MB -- --
    -- -- ++ ME -- Me ++ -- -- ME
    ME __ ME -- ++ -- __ -- ME --
    -- ++ -- -- SP SP -- Me -- --
    MB -- ME -- -- -- -- ++ ++ ++
    ++ ++ ++ -- Me -- Me __ -- ME
    -- -- ME __ -- ++ -- ++ ME --
    MB -- -- ME -- ++ -- ME -- MB
"""
MAP.weight_data = """
    10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5},
    {'battle': 6, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, J8, \
    = MAP.flatten()

step_on = SelectedGrids([C3])
road_boss = RoadGrids([C3, H4, [C5, C7], G6, G8])


class Config:
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 35
    EDGE_LINES_HOUGHLINES_THRESHOLD = 35
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.3
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
        if self.fleet_2_step_on(step_on, roadblocks=[road_boss]):
            return True

        if self.clear_roadblocks([road_boss]):
            return True
        if self.clear_potential_roadblocks([road_boss]):
            return True

        return self.battle_default()

    def battle_6(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.clear_roadblocks([road_boss])

        return self.fleet_boss.clear_boss()
