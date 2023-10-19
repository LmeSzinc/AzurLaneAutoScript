from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'H6'
MAP.camera_data = ['D3', 'D4', 'E4']
MAP.camera_data_spawn_point = ['D2']
MAP.map_data = """
    -- -- ME -- ME ++ ++ ++
    SP -- -- ME ME ME SP --
    -- ME -- ++ ++ -- ME --
    -- MM ME MA ++ ME MM ME
    ME ++ ++ -- MB -- ++ MB
    -- MB -- ++ ++ ME MB ME
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50
    50 50 40 40 40 40 50 50
    50 50 40 40 40 40 40 40
    10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 20
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1, 'mystery': 1},
    {'battle': 3, 'enemy': 2},
    {'battle': 4, 'enemy': 1, 'mystery': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
    = MAP.flatten()

step_on = SelectedGrids([C4, F4, A5, H4, F6])
road_boss = RoadGrids([B6, A6, A5, A4, B4, C4, D4, D5, E5, F5, F6, F4, G4, H4])


class Config:
    FLEET_BOSS = 1
    MAP_MYSTERY_HAS_CARRIER = True

    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    # EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.fleet_2_step_on(step_on, roadblocks=[road_boss]):
            return True

        if self.clear_roadblocks([road_boss]):
            return True

        self.clear_all_mystery()

        return self.battle_default()

    def battle_4(self):
        self.clear_all_mystery()

        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.clear_roadblocks([road_boss])

        return self.fleet_boss.clear_boss()
