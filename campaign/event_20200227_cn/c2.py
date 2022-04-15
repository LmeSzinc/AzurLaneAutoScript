from module.campaign.assets import C2 as ENTRANCE
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('c2')
MAP.shape = 'G7'
MAP.map_data = '''
    ME ++ -- -- ME -- MB
    ME ++ ME ME ++ ++ --
    MS -- SP -- ++ ++ --
    -- ME -- -- -- -- --
    ME ++ ++ -- SP ME ME
    -- ME ++ -- ME MS --
    MB -- -- -- ME -- ME
'''
MAP.weight_data = '''
    10 10 10 10 10 10 10
    10 10 10 10 10 10 10
    10 10 10 10 10 10 10
    10 10 10 10 10 10 10
    10 10 10 10 10 10 10
    10 10 10 10 10 10 10
    10 10 10 10 10 10 10
'''
# MAP.camera_data = ['D3', 'D5']
MAP.camera_data = ['C3', 'D5']
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'boss': 1},
]

A1, B1, C1, D1, E1, F1, G1, \
A2, B2, C2, D2, E2, F2, G2, \
A3, B3, C3, D3, E3, F3, G3, \
A4, B4, C4, D4, E4, F4, G4, \
A5, B5, C5, D5, E5, F5, G5, \
A6, B6, C6, D6, E6, F6, G6, \
A7, B7, C7, D7, E7, F7, G7, \
    = MAP.flatten()

ROAD_MAIN = RoadGrids([[E6, E7, F5, G5]])


class Config:
    MAP_HAS_AMBUSH = False
    CAMPAIGN_MODE = 'cd'
    # INTERNAL_LINES_HOUGHLINES_THRESHOLD = 60
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (150, 255 - 25),
        'width': 1,
        'prominence': 10,
        'distance': 50,
    }


class Campaign(CampaignBase):
    ENTRANCE = ENTRANCE
    MAP = MAP

    def battle_0(self):
        self.fleet_2.switch_to()
        if self.clear_roadblocks([ROAD_MAIN]):
            return True
        if self.clear_siren():
            return True

        if self.clear_enemy(scale=(3,)):
            return True
        return self.battle_default()

    battle_1 = battle_0

    def battle_2(self):
        if self.clear_enemy(strongest=True):
            return True

        return self.battle_default()

    battle_3 = battle_2

    def battle_4(self):

        self.fleet_1.switch_to()

        return self.clear_boss()

    def handle_in_stage(self):
        if self.appear(ENTRANCE):
            logger.info('In stage.')
            # self.device.sleep(0.5)
            self.ensure_no_info_bar(timeout=0.6)
            return True
        else:
            return False
