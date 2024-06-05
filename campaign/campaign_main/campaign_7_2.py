from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('7-2')
MAP.shape = 'H5'
MAP.camera_data = ['D2', 'D3']
MAP.camera_data_spawn_point = ['D2', 'D3']
MAP.map_data = """
    ME ++ ME -- ME ME -- SP
    MM ++ ++ MM -- -- ME --
    ME -- ME MB ME -- ME MM
    -- ME -- MM -- ME ++ ++
    SP -- ME ME -- ME ++ ++
"""
MAP.weight_data = """
    40 30 30 30 30 30 30 30
    20 20 20 10 20 20 20 20
    10 10 10 10 10 10 10 10
    20 20 20 10 20 20 20 20
    30 30 30 30 30 30 30 30
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3},
    {'battle': 1, 'enemy': 2, 'mystery': 1},
    {'battle': 2, 'enemy': 2, 'mystery': 1},
    {'battle': 3, 'enemy': 1, 'mystery': 2},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5 = MAP.flatten()

ROAD_MAIN = RoadGrids([A3, [C3, B4, C5], [F1, G2, G3]])
GRIDS_FOR_FASTER = SelectedGrids([A3, C3, E3, G3])
FLEET_2_STEP_ON = SelectedGrids([A3, G3, C3, E3])


class Config:
    SUBMARINE = 0


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.fleet_2_step_on(FLEET_2_STEP_ON, roadblocks=[ROAD_MAIN]):
            return True

        ignore = None
        if self.fleet_at(A3, fleet=2) and A1.enemy_scale != 3 and not self.fleet_at(A1, fleet=1):
            ignore = SelectedGrids([A2])
        if self.fleet_at(G3, fleet=2):
            ignore = SelectedGrids([H3])
        self.clear_all_mystery(nearby=False, ignore=ignore)

        if self.clear_roadblocks([ROAD_MAIN], strongest=True):
            return True

        if self.clear_enemy(scale=(3,)):
            return True
        if self.clear_potential_roadblocks([ROAD_MAIN], strongest=True):
            return True

        if self.clear_enemy(strongest=True):
            return True

        return self.battle_default()

    def battle_5(self):
        ignore = None
        if self.fleet_at(A3, fleet=2):
            ignore = SelectedGrids([A2])
        if self.fleet_at(G3, fleet=2):
            ignore = SelectedGrids([H3])
        self.clear_all_mystery(nearby=False, ignore=ignore)

        if self.clear_roadblocks([ROAD_MAIN]):
            return True

        if self.fleet_at(A3, fleet=2) and A2.is_mystery:
            self.fleet_2.clear_chosen_mystery(A2)
        if self.fleet_at(G3, fleet=2) and H3.is_mystery:
            self.fleet_2.clear_chosen_mystery(H3)

        return self.fleet_boss.clear_boss()
