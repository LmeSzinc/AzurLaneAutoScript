from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap

MAP = CampaignMap()
MAP.map_data = '''
    ++ ++ ++ -- ME -- -- -- -- ++ --
    -- ME -- ++ -- ++ ++ ME -- ++ ME
    ME -- -- ME -- ME ++ -- ME ++ --
    -- -- -- -- -- ++ ME -- -- -- SP
    ME -- -- ME -- -- -- __ -- -- SP
    -- -- ME ++ -- MS -- ME -- -- --
    -- -- -- ++ MB -- MB ++ ++ ++ ++
'''
MAP.camera_data = ['D3', 'D5', 'H3', 'H5']
MAP.weight_data = '''
    10 10 10 10 40 10 10 10 10 10 50
    10 30 10 10 10 10 10 20 10 10 50
    30 10 10 10 10 20 10 10 10 10 50
    10 10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10 10
    30 10 20 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10 10
'''
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'boss': 1},
]


class Config:
    SUBMARINE = 0

    POOR_MAP_DATA = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_SIREN = True
    MAP_HAS_DYNAMIC_RED_BORDER = False
    MAP_HAS_MAP_STORY = True
    MAP_SIREN_TEMPLATE = ['Z18']
    MAP_SIREN_COUNT = 1

    TRUST_EDGE_LINES = False
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (100, 255 - 24),
        'width': 1,
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 24, 255),
        'prominence': 2,
        'distance': 50,
        'wlen': 1000
    }


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.fleet_2_break_siren_caught():
            return True

        return self.battle_default()

    def battle_4(self):
        return self.fleet_boss.clear_boss()
