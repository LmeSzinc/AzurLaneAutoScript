from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('SP')
MAP.shape = 'G10'
MAP.camera_data = ['D2', 'D6', 'D8']
MAP.camera_data_spawn_point = ['D8']
MAP.map_data = """
    -- ++ ++ MB ++ ++ --
    ++ ++ ++ -- ++ ++ ++
    ME -- -- -- -- -- ME
    ++ ++ ++ -- ++ ++ ++
    ME -- -- -- -- -- ME
    ++ ++ ++ -- ++ ++ ++
    MS -- ++ MS ++ -- MS
    ++ -- ++ -- ++ -- ++
    -- -- -- __ -- -- --
    -- -- SP -- SP -- --
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
    50 50 50 50 50 50 50
    50 50 50 50 50 50 50
"""
# MAP.maze_data = [('D6', 'B8', 'F8'), ('D4', 'C5', 'E5'), ('D2', 'C3', 'E3', 'D8')]
MAP.spawn_data = [
    {'battle': 0, 'enemy': 4, 'siren': 3},
    {'battle': 1},
    {'battle': 2},
    {'battle': 3},
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
A9, B9, C9, D9, E9, F9, G9, \
A10, B10, C10, D10, E10, F10, G10, \
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

    # MAP_HAS_MAZE = True
    MAP_HAS_SIREN = True
    MAP_SIREN_TEMPLATE = ['Warspite', 'Formidable', 'Illustrious']
    MAP_SWIPE_MULTIPLY = 1.472
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.423
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    # EDGE_LINES_HOUGHLINES_THRESHOLD = 40


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.clear_chosen_enemy(D7, expected='siren')
        return True

    def battle_1(self):
        self.goto(C9)
        self.goto(B9)
        self.clear_chosen_enemy(A7, expected='siren')
        return True

    def battle_2(self):
        self.clear_chosen_enemy(G7, expected='siren')
        return True

    def battle_3(self):
        self.goto(D5)
        self.clear_chosen_enemy(A5)
        return True

    def battle_4(self):
        self.clear_chosen_enemy(G5)
        return True

    def battle_5(self):
        self.goto(D3)
        self.clear_chosen_enemy(A3)
        return True

    def battle_6(self):
        self.clear_chosen_enemy(G3)
        return True

    def battle_7(self):
        if self.fleet_boss_index == 2:
            self.fleet_boss.switch_to()
            self.goto(D7)
            self.goto(D5)
            self.goto(D6)
            self.goto(D5)
            self.goto(D3)
            self.goto(D4)
            self.goto(D3)
            self.clear_chosen_enemy(D1, expected='boss')
        else:
            self.clear_chosen_enemy(D1, expected='boss')
        return True
