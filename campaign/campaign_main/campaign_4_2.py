from campaign.campaign_main.campaign_4_1 import Config
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'F6'
MAP.camera_data = ['D2', 'D4']
MAP.camera_data_spawn_point = ['D2']
# WIKI的图有错: https://wiki.biligame.com/blhx/4-2
# D5是敌人刷新点, 假图害人
MAP.map_data = """
    ++ ++ ++ ME SP --
    SP -- -- -- ME --
    -- -- ME ME -- ME
    SP -- -- -- -- MB
    ++ ++ ME ME -- ME
    ++ ++ -- MB ME MM
"""
MAP.weight_data = """
    50 50 50 50 50 50
    50 50 50 50 50 50
    50 50 50 50 50 50
    50 50 50 10 10 10
    50 50 20 10 10 20
    50 50 20 10 10 20
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 3, 'mystery': 1},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, \
A2, B2, C2, D2, E2, F2, \
A3, B3, C3, D3, E3, F3, \
A4, B4, C4, D4, E4, F4, \
A5, B5, C5, D5, E5, F5, \
A6, B6, C6, D6, E6, F6, \
    = MAP.flatten()


class Campaign(CampaignBase):
    MAP = MAP
    MAP_AMBUSH_OVERLAY_TRANSPARENCY_THRESHOLD = 0.3
    MAP_AIR_RAID_OVERLAY_TRANSPARENCY_THRESHOLD = 0.25
    MAP_ENEMY_SEARCHING_OVERLAY_TRANSPARENCY_THRESHOLD = 0.65

    def battle_0(self):
        self.clear_all_mystery()

        return self.battle_default()

    def battle_3(self):
        self.clear_all_mystery()

        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.battle_default()

        return self.fleet_boss.clear_boss()
