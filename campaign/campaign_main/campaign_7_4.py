from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('7-4')
MAP.shape = 'H6'
MAP.camera_data = ['C2', 'C4', 'E2', 'E4']
MAP.camera_data_spawn_point = ['D2', 'D4']
MAP.map_data = """
    MB ME ME -- ++ ++ ++ MB
    ME __ -- ME SP -- SP --
    -- ++ ME -- -- ME -- ME
    ME ++ ++ ++ ME -- ME --
    SP -- MA ++ ME ++ __ ME
    MM -- MM ME -- ME MB --
"""
MAP.weight_data = """
    10 20 50 10 10 10 10 10
    04 10 10 07 10 10 10 10
    10 10 05 10 10 40 10 20
    04 50 50 50 30 10 06 10
    50 50 50 50 30 10 10 20
    50 50 50 50 30 30 10 30
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 3, 'mystery': 1},
    {'battle': 3, 'enemy': 2, 'mystery': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
    = MAP.flatten()

road_a1 = RoadGrids([A2 , [C3, D2]])
road_g6 = RoadGrids([G4]) 
roads = [road_a1, road_g6]

fleet_2_step_on = SelectedGrids([A4, A2, G4, D2, C3])
road_a5 = RoadGrids([A4, A2, [C3, D2]]) \
    .combine(RoadGrids([G4]))


class Config:
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    # EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.fleet_2_step_on(fleet_2_step_on, roadblocks=[road_a5]):
            return True

        self.clear_all_mystery()

        if self.clear_roadblocks(roads):
            return True
        if self.clear_potential_roadblocks(roads):
            return True

        return self.battle_default()

    def battle_3(self):
        if self.fleet_2_step_on(fleet_2_step_on, roadblocks=[road_a5]):
            return True

        self.clear_all_mystery()

        if self.fleet_boss_index == 1:
            self.pick_up_ammo()

        if self.clear_roadblocks(roads):
            return True
        if self.clear_potential_roadblocks(roads):
            return True

        return self.battle_default()

    def battle_5(self):
        return self.fleet_boss.clear_boss()
