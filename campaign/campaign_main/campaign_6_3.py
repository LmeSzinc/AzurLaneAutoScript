from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'H5'
MAP.camera_data = ['D3', 'E2']
MAP.camera_data_spawn_point = ['D3', 'E2']
# WIKI的图有错: https://wiki.biligame.com/blhx/6-3
# G3是出生点, 假图害人
MAP.map_data = """
    MB -- ME SP -- ME ME MM
    ME -- -- ++ ++ -- ME --
    -- -- ME MB ++ ME SP MB
    SP -- ME -- ME -- ME ME
    ++ ME -- ME SP ME -- MM
"""
MAP.weight_data = """
    10 10 50 50 50 50 50 10
    50 10 10 10 10 50 50 10
    50 50 10 10 10 20 10 10
    50 50 10 10 10 10 10 30
    50 50 20 20 20 20 10 10
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 4},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 2, 'mystery': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'mystery': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
    = MAP.flatten()

step_on = SelectedGrids([E4, G2, C3, C4, F3])
road_boss = RoadGrids([
    A1, [B1, A2], B2, [C2, B3], [B3, C3], [B4, C3], [C3, C4], [C4, D3], D4,  # A1 - D4
    [G3, H4], [G3, G4], G3, [F3, G4], F4, [E4, F5], [E4, E5], [E4, D5]  # H3 - D4
])
road_in_map = RoadGrids([
    A1, [B1, A2], B2, [C2, B3], [B3, C3], [B4, C3], [C3, C4], [C4, D3], D4,  # A1 - D4
    [G3, H4], [G3, G4], G3, [F3, G4], F4, [E4, F5], [E4, E5], [E4, D5],  # H3 - D4
    D1, C1, [B1, C2],  # D1 - C2
    E1, F1, [G1, F2], [G2, F2], [F3, G2]  # E1 - G3
])
road_mystery = RoadGrids([[F5, G4], [H4, G5], H2])


class Config:
    FLEET_BOSS = 1
    MAP_MYSTERY_HAS_CARRIER = True

    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    # EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.fleet_2_step_on(step_on, roadblocks=[road_in_map]):
            return True

        if self.clear_roadblocks([road_boss]):
            return True
        if self.clear_roadblocks([road_mystery]):
            return True
        self.clear_all_mystery()
        if self.clear_potential_roadblocks([road_boss]):
            return True
        if self.clear_potential_roadblocks([road_mystery]):
            return True

        return self.battle_default()

    def battle_4(self):
        self.clear_all_mystery()

        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.clear_roadblocks([road_boss])

        return self.fleet_boss.clear_boss()
