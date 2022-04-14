from campaign.campaign_main.campaign_12_1 import Config as ConfigBase
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap('12-4')
MAP.shape = 'K8'
MAP.camera_data = ['D2', 'D6', 'H2', 'H6']
MAP.camera_data_spawn_point = ['D6']
MAP.map_data = """
    MB MB ME -- ME ++ ++ ++ MB MB ++
    ME ++ -- ME -- MA ++ ++ ME Me ++
    -- ME __ Me Me -- Me Me -- Me --
    ++ -- ME ++ ++ Me ME __ ++ ++ ME
    ++ ME ME -- ME ME -- ME -- ++ --
    ++ __ Me Me -- Me ME ++ __ -- ME
    ME -- Me -- Me -- Me -- -- ME --
    -- -- -- ME SP SP ++ ++ ++ ME --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
    50 50 50 50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5},
    {'battle': 6, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, I1, J1, K1, \
A2, B2, C2, D2, E2, F2, G2, H2, I2, J2, K2, \
A3, B3, C3, D3, E3, F3, G3, H3, I3, J3, K3, \
A4, B4, C4, D4, E4, F4, G4, H4, I4, J4, K4, \
A5, B5, C5, D5, E5, F5, G5, H5, I5, J5, K5, \
A6, B6, C6, D6, E6, F6, G6, H6, I6, J6, K6, \
A7, B7, C7, D7, E7, F7, G7, H7, I7, J7, K7, \
A8, B8, C8, D8, E8, F8, G8, H8, I8, J8, K8, \
    = MAP.flatten()


class Config(ConfigBase):
    ENABLE_AUTO_SEARCH = False


class Campaign(CampaignBase):
    MAP = MAP
    s3_enemy_count = 0
    non_s3_enemy_count = 0

    def check_s3_enemy(self):
        if self.battle_count == 0:
            self.s3_enemy_count = 0
            self.non_s3_enemy_count = 0

        current = self.map.select(is_enemy=True, enemy_scale=3).count
        logger.attr('S3_enemy', current)

        if self.battle_count == self.config.C124LargeLeveling_NonLargeEnterTolerance \
                and self.config.C124LargeLeveling_NonLargeRetreatTolerance < 10:
            if self.s3_enemy_count + current == 0:
                self.withdraw()
        elif self.battle_count > self.config.C124LargeLeveling_NonLargeEnterTolerance:
            if self.non_s3_enemy_count >= self.config.C124LargeLeveling_NonLargeRetreatTolerance and current == 0:
                self.withdraw()

    def battle_0(self):
        self.check_s3_enemy()

        if self.battle_count >= self.config.C124LargeLeveling_PickupAmmo:
            self.pick_up_ammo()

        if self.clear_enemy(scale=(3,), genre=['light', 'carrier', 'enemy', 'treasure', 'main']):
            self.s3_enemy_count += 1
            self.non_s3_enemy_count = 0
            return True
        if self.clear_enemy(scale=[2, 1]):
            self.non_s3_enemy_count += 1
            return True
        if not self.map.select(is_enemy=True, may_boss=False):
            logger.info('No more enemies.')
            self.withdraw()

        return self.battle_default()
