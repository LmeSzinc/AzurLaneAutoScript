from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap

MAP = CampaignMap()
MAP.map_data = '''
    -- ME ++ ++ -- ME
    ME ME ++ ++ ME ME
    ++ -- MB MB -- --
    ME -- ME ME ++ ME
    ME MS __ __ ME ME
    ++ ++ MS -- MS ME
    ++ MS -- ME ++ ME
    ME -- SP -- ME --
    ME -- SP SP -- ME
'''
MAP.weight_data = """
    50 50 50 50 50 50
    40 40 40 40 40 40
    40 40 10 10 40 40
    30 20 20 20 30 50
    30 20 20 20 30 50
    30 30 20 20 30 50
    30 20 20 20 30 50
    50 20 20 20 30 50
    50 20 20 20 20 50
"""
MAP.camera_data = ['C3', 'C5', 'C7']
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 2},
    {'battle': 5, 'enemy': 1, 'boss': 1},
]


class Config:
    SUBMARINE = 0
    FLEET_BOSS = 2

    POOR_MAP_DATA = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_SIREN = True
    MAP_HAS_DYNAMIC_RED_BORDER = False
    MAP_HAS_MAP_STORY = True
    MAP_SIREN_TEMPLATE = ['Algerie', 'LaGalissonniere']
    MAP_SIREN_COUNT = 2

    TRUST_EDGE_LINES = False
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (100, 255 - 16),
        'width': 1,
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 16, 255),
        'prominence': 2,
        'distance': 50,
        'wlen': 1000
    }


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(scale=(1,)):
            return True
        if self.clear_enemy(scale=(2,), genre=['light', 'main', 'enemy', 'carrier']):
            return True
        if self.clear_enemy(genre=['light', 'main', 'enemy']):
            return True

        return self.battle_default()

    def battle_5(self):
        return self.fleet_boss.brute_clear_boss()
