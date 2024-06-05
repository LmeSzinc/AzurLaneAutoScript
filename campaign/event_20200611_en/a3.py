from campaign.event_20200611_en.a1 import Config as ConfigBase
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'H7'
MAP.map_data = '''
    -- ME ME ++ ++ ME ME ME
    ME -- -- MS -- -- MB --
    ++ ++ -- ME __ ME ++ ++
    ME ME -- ++ -- ME ++ ++
    ME -- -- ++ -- MS MB ME
    SP SP -- -- __ -- ME ++
    -- SP ME ++ ME MS -- ME
'''
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 1},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1, 'boss': 1},
]


class Config(ConfigBase):
    POOR_MAP_DATA = False


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

    def battle_4(self):
        return self.fleet_boss.clear_potential_boss()
