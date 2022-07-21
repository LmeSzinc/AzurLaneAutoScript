from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('9-2')
MAP.shape = 'H5'
MAP.camera_data = ['E3']
MAP.camera_data_spawn_point = ['D1', 'D3']
MAP.map_data = """
    SP -- ++ ++ ++ Me -- MB
    ++ -- ++ ++ ++ ME ++ ++
    -- ME -- ME ME Me ++ ++
    -- -- ++ -- ME ++ ME MB
    SP SP ++ ME -- Me ME ME
"""
MAP.weight_data = """
    90 90 90 90 90 30 30 30
    90 90 90 90 90 30 90 90
    90 80 70 60 50 30 90 90
    90 90 90 90 50 90 30 30
    90 90 90 90 40 40 30 30
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
    = MAP.flatten()

# Might have wrong prediction on D5
MAP.ignore_prediction(D5, enemy_scale=1, enemy_genre='Enemy')
road_main = RoadGrids([B3, D3, [D5, E4], F5, G5, [G4, H5], H4, E3, F3, F2, F1])
step_on = SelectedGrids([F3, E4])


class Config:
    SUBMARINE = 0
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.fleet_2_step_on(step_on, roadblocks=[road_main]):
            return True

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

        return self.fleet_2.clear_boss()
