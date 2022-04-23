from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('d1')
MAP.shape = 'H6'
MAP.map_data = '''
    ++ ++ ++ -- -- -- -- MB
    MS -- -- -- __ ME ME --
    ME -- ME ++ ++ MS -- --
    SP -- ME ++ ++ MS ME --
    ME -- -- -- -- -- -- --
    SP -- -- ME MS ME -- MB
'''


class Config:
    SUBMARINE = 0
    FLEET_BOSS = 0

    POOR_MAP_DATA = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_FLEET_STEP = True
    MAP_HAS_MOVABLE_ENEMY = True
    MAP_HAS_SIREN = True
    MAP_HAS_DYNAMIC_RED_BORDER = True
    MAP_SIREN_COUNT = 4


class Campaign(CampaignBase):
    MAP = MAP

