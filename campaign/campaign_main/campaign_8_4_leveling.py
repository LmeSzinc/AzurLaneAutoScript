from .campaign_8_4 import Campaign as CampaignBase
from .campaign_8_4 import Config as ConfigBase
from .campaign_8_4 import *


class Config(ConfigBase):
    ENABLE_AUTO_SEARCH = False


class Campaign(CampaignBase):
    def battle_0(self):
        self.fleet_2_push_forward()

        self.clear_all_mystery()
        if self.map.select(is_mystery=True, is_accessible_1=False, is_accessible_2=True):
            self.fleet_2.clear_all_mystery()
            self.fleet_2_push_forward()

        if self.clear_roadblocks([road_D7, road_F3, road_main], strongest=True):
            return True
        if self.clear_potential_roadblocks([road_D7, road_F3, road_main], scale=(3,)):
            return True
        if self.clear_enemy(scale=(3,)):
            return True
        if self.clear_potential_roadblocks([road_D7, road_F3, road_main], strongest=True):
            return True
        if self.clear_first_roadblocks([road_D7, road_F3, road_main]):
            return True

        return self.battle_default()

    def battle_4(self):
        self.clear_all_mystery()
        if self.map.select(is_mystery=True, is_accessible_1=False, is_accessible_2=True):
            self.fleet_2.clear_all_mystery()
            self.fleet_2_push_forward()

        return self.brute_clear_boss()
