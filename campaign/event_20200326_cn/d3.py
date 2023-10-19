from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'G9'
MAP.map_data = '''
    ME -- ME -- ME -- ME
    ++ -- -- ME -- -- ++
    ++ -- ++ ++ ++ -- ++
    MS -- MB MB MB -- MS
    ME ME -- __ -- ME ME
    ++ ++ SP -- SP ++ ++
    ++ ME -- -- -- ME ++
    ME -- -- ME -- -- ME
    -- MS ME -- ME MS --
'''
MAP.camera_data = ['D3', 'D5', 'D7']
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2, 'siren': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5, 'enemy': 1},
    {'battle': 6, 'enemy': 1, 'boss': 1},
]
MAP.in_map_swipe_preset_data = (0, 2)


A1, B1, C1, D1, E1, F1, G1, \
A2, B2, C2, D2, E2, F2, G2, \
A3, B3, C3, D3, E3, F3, G3, \
A4, B4, C4, D4, E4, F4, G4, \
A5, B5, C5, D5, E5, F5, G5, \
A6, B6, C6, D6, E6, F6, G6, \
A7, B7, C7, D7, E7, F7, G7, \
A8, B8, C8, D8, E8, F8, G8, \
A9, B9, C9, D9, E9, F9, G9, \
    = MAP.flatten()


class Config:
    MAP_HAS_AMBUSH = False
    CAMPAIGN_MODE = 'hard'

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (100, 220),
        'width': 1,
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 80, 255),
        'prominence': 2,
        'distance': 50,
        # 'width': (0, 7),
        'wlen': 1000
    }


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(scale=(3,)):
            return True

        return self.battle_default()

    def battle_5(self):
        if self.clear_enemy(scale=(1,)):
            return True
        if self.clear_enemy(scale=(2,)):
            return True

        return self.battle_default()

    def battle_6(self):
        return self.fleet_boss.clear_boss()
