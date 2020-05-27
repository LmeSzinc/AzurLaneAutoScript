from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap

MAP = CampaignMap('a3')
MAP.shape = 'K7'
MAP.map_data = '''
    SP ++ ++ ++ ME -- -- -- ME -- MM
    -- -- -- -- -- -- ME -- -- -- --
    ME -- ++ ME -- -- -- -- ++ ++ --
    ME -- -- -- MS ++ __ -- MB ++ --
    -- -- ME -- -- -- -- -- -- -- --
    -- -- ++ ++ ME ME -- ME ++ ++ ++
    SP -- ++ ++ ME -- -- -- -- ME MM
'''

class Config:
    SUBMARINE = 1
    FLEET_BOSS = 1
    POOR_MAP_DATA = True
    MAP_HAS_AMBUSH = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_MOVABLE_ENEMY = False
    MAP_HAS_SIREN = True
    MAP_HAS_DYNAMIC_RED_BORDER = False
    MAP_HAS_MAP_STORY = False
    MAP_SIREN_COUNT = 1

class Campaign(CampaignBase):
    MAP = MAP

