from module.campaign.assets import EVENT_20200312CN_SP3 as ENTRANCE
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids
from module.ui.assets import CAMPAIGN_GOTO_DAILY

MAP = CampaignMap('d3')
MAP.shape = 'I6'
MAP.map_data = '''
    ++ MB -- ME -- ME -- ++ ++
    MB -- -- -- ++ -- ME ++ ++
    MB ME -- -- -- ME -- ME SP
    ++ ++ ++ -- -- -- -- ++ --
    MB -- ME ME -- ++ -- ME --
    -- ME -- -- SP ++ -- -- --
'''
MAP.weight_data = '''
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10
'''
MAP.camera_data = ['D2', 'D4', 'F2', 'F4']
# MAP.camera_data = ['D3', 'D5']
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'boss': 1},
]

A1, B1, C1, D1, E1, F1, G1, H1, I1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, \
    = MAP.flatten()

ROAD_MAIN = RoadGrids([[B6, C5]])


class Config:
    MAP_HAS_AMBUSH = False
    CAMPAIGN_MODE = 'normal'  # A sp map can treat as normal map.
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (120, 255 - 40),
        'width': 2,
        'prominence': 10,
        'distance': 35,
    }


class Campaign(CampaignBase):
    ENTRANCE = ENTRANCE
    MAP = MAP

    def battle_0(self):
        if self.clear_roadblocks([ROAD_MAIN]):
            return True
        if self.clear_potential_roadblocks([ROAD_MAIN]):
            return True

        if self.clear_enemy(scale=(1,)):
            return True
        if self.clear_enemy(scale=(2,)):
            return True

        return self.battle_default()

    battle_1 = battle_0
    battle_2 = battle_0
    battle_3 = battle_0
    battle_4 = battle_0

    def battle_5(self):
        return self.fleet_boss.clear_boss()

    def handle_in_stage(self):
        """
        SP map don't have normal/hard switch button,
        so overwrite handle_in_stage method in module.map.map_operation.
        """
        if self.appear(CAMPAIGN_GOTO_DAILY) and self.appear(ENTRANCE):
            logger.info('In stage.')
            self.ensure_no_info_bar(timeout=0.6)
            return True
        else:
            return False
