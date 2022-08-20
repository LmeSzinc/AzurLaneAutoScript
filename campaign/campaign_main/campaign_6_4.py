from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'H6'
MAP.camera_data = ['D2', 'D4', 'E2', 'E4']
MAP.camera_data_spawn_point = ['D2', 'D4']
MAP.map_data = """
    -- ME MB MB -- ME ++ ++
    MB SP ME -- ME MM MA ++
    -- ++ ME -- -- ME SP ME
    ME __ -- ME ME __ ME MB
    -- ME -- MB ++ ME -- ME
    MB ME -- SP -- ME -- --
"""
MAP.weight_data = """
    50 40 40 40 50 50 50 50
    40 40 20 20 20 20 50 50
    10 50 10 10 10 10 10 20
    10 10 10 10 30 30 30 40
    10 20 20 40 40 50 50 50
    30 40 30 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 4},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1, 'mystery': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
    = MAP.flatten()

step_on = SelectedGrids([C2, C3, D4, F3, G4])
road_boss = RoadGrids([
    [A5, B6], [A4, B5, B6], C4, C5, [C3, D4], D3,  # A6 - D3
    [C5, D3],  # D5 - D3
    [B1, B2], [B1, C2], [C1, C2], [C2, D1], [C2, D2],  # A2 - D3
    [H3, G4], [G3, G4], [F3, G4], [F3, F4], [F2, F3, E4], [E2, F3, E4], E3  # H4 - D3
])


class Config:
    FLEET_BOSS = 1
    MAP_MYSTERY_HAS_CARRIER = True


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.fleet_2_step_on(step_on, roadblocks=[road_boss]):
            return True

        if self.clear_roadblocks([road_boss]):
            return True
        self.clear_all_mystery()
        if self.clear_potential_roadblocks([road_boss]):
            return True

        return self.battle_default()

    def battle_5(self):
        self.clear_all_mystery()

        if self.config.FLEET_BOSS == 1:
            self.pick_up_ammo()

        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.clear_roadblocks([road_boss])

        return self.fleet_boss.clear_boss()
