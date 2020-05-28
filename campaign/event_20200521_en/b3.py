from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger


MAP = CampaignMap('b3')
MAP.shape = 'I9'
MAP.map_data = '''
    SP -- ++ ++ -- -- -- ME --
    -- ME ++ ++ -- ME -- -- --
    -- -- -- -- -- -- ME ME --
    ME -- ME ME -- ME ++ ++ ++
    -- -- ++ __ -- -- -- MB ++
    -- ME ++ -- -- ME ++ ++ ++
    -- -- MS -- ++ ME -- ME --
    SP -- -- -- ++ -- -- ME --
    SP -- MS -- -- ME -- -- -- 
'''

class Config:
    SUBMARINE = 1
    POOR_MAP_DATA = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_MOVABLE_ENEMY = False
    MAP_HAS_SIREN = True
    MAP_HAS_DYNAMIC_RED_BORDER = False
    MAP_SIREN_COUNT = 2


class Campaign(CampaignBase):
    MAP = MAP


