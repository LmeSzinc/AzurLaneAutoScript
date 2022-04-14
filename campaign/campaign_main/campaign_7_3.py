from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('7-3')
MAP.shape = 'H6'
MAP.camera_data = ['D2', 'D4', 'E2', 'E4']
MAP.camera_data_spawn_point = ['E4']
MAP.map_data = """
    MB ME -- -- ME -- ME MB
    ME MM ++ ME -- ME MM ME
    -- ME -- SP -- ++ ++ ++
    ME -- ME -- SP -- ++ ++
    MM ++ ++ ++ MM ME ++ MB
    ME ME MB ++ ME -- ME ME
"""
MAP.weight_data = """
    10 40 30 30 20 20 20 10
    30 30 10 30 20 30 30 40
    30 20 10 10 10 10 10 10
    20 20 30 10 10 10 10 10
    30 10 10 10 10 20 10 10
    30 40 10 10 20 20 30 40
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2, 'mystery': 1},
    {'battle': 2, 'enemy': 2, 'mystery': 1},
    {'battle': 3, 'enemy': 2, 'mystery': 1},
    {'battle': 4, 'enemy': 1, 'mystery': 1},
    {'battle': 5, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
    = MAP.flatten()

# road_a1 = RoadGrids([[A2, B1], [A2, B3], [B3, A4], [A4, B3, D2, E1], [C4, B3, D2, E1]])
road_a1 = RoadGrids([[A2, B1], [A2, B3], [B3, A4], [B3, C4]]) \
    .combine(RoadGrids([A2, [E1, D2]]))
road_c6 = RoadGrids([B6, A6, A4, [B3, C4]])
road_h1 = RoadGrids([[H2, G1], [G1, F2], [F2, E1]])
road_h5 = RoadGrids([H6, G6, [E6, F5]])
roads = [road_a1, road_c6, road_h1, road_h5]
fleet_2_step_on = SelectedGrids([A4, B3, E1, F5])


class Config:
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    # EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.fleet_2_step_on(fleet_2_step_on, roadblocks=roads):
            return True

        self.clear_all_mystery()

        if self.clear_roadblocks(roads):
            return True
        if self.clear_potential_roadblocks(roads):
            return True

        return self.battle_default()

    def battle_5(self):
        self.clear_all_mystery()

        boss = self.map.select(is_boss=True)
        if boss:
            boss = boss[0]
            if boss == A1:
                road_boss = [road_a1]
            elif boss == C6:
                road_boss = [road_c6]
            elif boss == H1:
                road_boss = [road_h1]
            elif boss == H5:
                road_boss = [road_h5]
            else:
                logger.warning(f'Unexpected boss grid: {boss}')
                road_boss = roads

            if not self.check_accessibility(boss, fleet='boss'):
                return self.clear_roadblocks(road_boss)

        return self.fleet_boss.clear_boss()
