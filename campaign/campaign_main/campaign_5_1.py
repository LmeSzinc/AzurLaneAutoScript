from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'H6'
MAP.camera_data = ['D2', 'D4']
MAP.camera_data_spawn_point = ['D2', 'D4']
MAP.map_data = """
    MB MM ME ++ ++ ++ ++ ++
    SP -- -- -- ME -- -- MB
    -- -- ME ME -- -- SP ME
    -- ME -- ME -- ME ME MB
    SP -- ME -- -- -- ++ ++
    MB ME -- ME -- MA ++ ++
"""
MAP.weight_data = """
    10 10 50 50 50 50 50 50
    10 10 10 10 10 10 10 10
    10 20 20 20 10 10 10 10
    10 20 20 20 10 50 10 10
    10 10 10 10 10 50 50 50
    10 20 20 20 20 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3, 'mystery': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
    = MAP.flatten()


class Config:
    FLEET_BOSS = 1
    MAP_MYSTERY_HAS_CARRIER = True

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
    HOMO_EDGE_COLOR_RANGE = (0, 49)


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        self.clear_all_mystery()

        return self.battle_default()

    def battle_4(self):
        self.clear_all_mystery()

        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.battle_default()

        return self.fleet_boss.clear_boss()
