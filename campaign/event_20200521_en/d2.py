from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap

MAP = CampaignMap('d2')
MAP.shape = 'I7'
MAP.map_data = '''
    SP -- -- -- -- -- ME ++ MB 
    -- ME -- MS ME -- -- ++ -- 
    -- -- ME ++ ++ ++ -- -- -- 
    ME __ -- ME ME ME -- MS -- 
    ME MS -- ++ ++ ++ -- -- -- 
    -- ME -- ME -- -- -- ++ -- 
    SP -- -- -- -- ME -- ++ MB 
'''

MAP.camera_data = ['D2', 'B5', 'H4']
MAP.weight_data = """
    40 40 40 40 40 40 30 40 20
    40 30 40 10 30 40 40 40 40
    40 40 30 40 40 40 40 40 40
    30 30 40 30 30 30 40 10 40
    30 10 40 40 40 40 40 40 40
    40 30 40 30 40 40 40 40 40
    40 40 40 40 40 30 40 40 20
"""

class Config:
    CAMPAIGN_MODE = 'hard'
    SUBMARINE = 1
    FLEET_BOSS = 2
    POOR_MAP_DATA = False
    MAP_HAS_AMBUSH = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_MOVABLE_ENEMY = False
    MAP_HAS_SIREN = True
    MAP_HAS_DYNAMIC_RED_BORDER = False
    MAP_HAS_MAP_STORY = False
    MAP_SIREN_COUNT = 3

class Campaign(CampaignBase):
    MAP = MAP
