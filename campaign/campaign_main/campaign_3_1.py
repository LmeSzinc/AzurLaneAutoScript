from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'G4'
MAP.camera_data = ['D2']
MAP.camera_data_spawn_point = ['D1', 'D2']
MAP.map_data = """
    SP -- ME -- ME MB --
    -- ME -- ME -- ME MB
    ++ ++ ME -- ME -- --
    ++ ++ SP ME MM ++ ++
"""
MAP.weight_data = """
    30 30 30 20 10 10 10
    30 30 30 20 10 09 10
    40 40 40 20 10 10 10
    40 40 40 20 20 10 10
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'mystery': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 2, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, \
A2, B2, C2, D2, E2, F2, G2, \
A3, B3, C3, D3, E3, F3, G3, \
A4, B4, C4, D4, E4, F4, G4, \
    = MAP.flatten()


class Config:
    FLEET_BOSS = 1
    MAP_MYSTERY_HAS_CARRIER = True

    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 75
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (120, 255 - 49),
        'width': (1.5, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 49, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }
    HOMO_CANNY_THRESHOLD = (75, 100)
    HOMO_EDGE_COLOR_RANGE = (0, 49)


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.fleet_2_push_forward()

        if self.fleet_2_rescue(G2):
            return True

        self.clear_all_mystery()

        return self.battle_default()

    def battle_3(self):
        self.clear_all_mystery()

        if not self.check_accessibility(G2, fleet='boss'):
            return self.fleet_boss.battle_default()

        return self.fleet_boss.clear_boss()
