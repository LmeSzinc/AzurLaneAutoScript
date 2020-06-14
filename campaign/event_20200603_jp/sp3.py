from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from campaign.event_20200603_cn.sp1 import Config as ConfigBase

MAP = CampaignMap()
MAP.map_data = '''
    ++ ++ ++ MS ++ ME -- ME ++ ++ ++
    SP -- -- -- -- -- MS -- ME ME --
    SP -- -- -- -- ME -- __ -- -- ME
    ++ ++ ++ MS -- ++ ++ -- ME ++ --
    MB MB ++ -- ME ++ ++ -- -- ++ ++
    -- -- -- -- -- -- -- -- -- ME --
    ME ME -- ME -- ME ++ ME -- ME --
'''
MAP.camera_data = ['D3', 'D5', 'G3', 'G5']
MAP.weight_data = '''
    10 10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10 10
    10 10 10 10 10 10 10 10 10 10 10
'''
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3, 'siren': 2},
    {'battle': 1, 'enemy': 2, 'siren': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'boss': 1},
]


class Config(ConfigBase):
    FLEET_BOSS = 2

    # POOR_MAP_DATA = True
    MAP_SIREN_TEMPLATE = ['Z19']
    MAP_SIREN_COUNT = 2


class Campaign(CampaignBase):
    MAP = MAP

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.fleet_2_break_siren_caught():
            return True

        return self.battle_default()

    def battle_5(self):
        return self.fleet_2.clear_boss()
