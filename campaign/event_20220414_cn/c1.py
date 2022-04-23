from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('C1')
MAP.shape = 'I7'
MAP.camera_data = ['D2', 'D5', 'F2', 'F5']
MAP.camera_data_spawn_point = ['D2', 'D5']
MAP.map_data = """
    ++ ++ MS ME Me ++ ME -- --
    ++ ME -- -- -- -- -- Me --
    SP -- Me ++ ++ ++ -- -- ME
    -- -- -- MB -- MB -- ++ ++
    SP -- -- -- __ -- MS ++ ++
    -- ++ Me MS ++ ++ -- ME --
    ME -- ME -- -- ME -- ME --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_SIREN_TEMPLATE = ['U81', 'U101', 'U522']
    MOVABLE_ENEMY_TURN = (2,)
    MAP_HAS_SIREN = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====

    DETECTION_BACKEND = 'homography'
    HOMO_STORAGE = ((7, 6), [(263.285, 83.378), (1045.503, 83.378), (149.679, 616.57), (1168.955, 616.57)])
    HOMO_EDGE_COLOR_RANGE = (0, 13)
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 350
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    MAP_SWIPE_MULTIPLY = 1.689
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.633


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True

        return self.battle_default()

    def battle_4(self):
        return self.clear_boss()
