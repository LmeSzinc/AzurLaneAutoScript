from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from .campaign_base import CampaignBase

MAP = CampaignMap('VSP')
MAP.shape = 'G8'
MAP.camera_data = ['D2', 'D6']
MAP.camera_data_spawn_point = ['D6']
MAP.map_data = """
    ++ ++ ++ MB ++ ++ ++
    ME -- MS -- MS -- ME
    ++ ++ -- MS -- ++ ++
    ++ ME -- ++ -- ME ++
    ++ ++ -- ++ -- ++ ++
    ++ ++ -- __ -- ++ ++
    ME -- -- -- -- -- ME
    ++ ++ SP -- SP ++ ++
"""
MAP.weight_data = """
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'siren': 3},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 2},
    {'battle': 4},
    {'battle': 5},
    {'battle': 6},
    {'battle': 7, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, \
A2, B2, C2, D2, E2, F2, G2, \
A3, B3, C3, D3, E3, F3, G3, \
A4, B4, C4, D4, E4, F4, G4, \
A5, B5, C5, D5, E5, F5, G5, \
A6, B6, C6, D6, E6, F6, G6, \
A7, B7, C7, D7, E7, F7, G7, \
A8, B8, C8, D8, E8, F8, G8, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = False
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    # ===== End of generated config =====

    MAP_HAS_SIREN = True
    MAP_SIREN_TEMPLATE = ['AzusaMiura', 'ChihayaKisaragi', 'IoriMinase']
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    HOMO_EDGE_COLOR_RANGE = (0, 12)


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True

        return self.battle_default()

    def battle_7(self):
        return self.fleet_boss.clear_boss()
