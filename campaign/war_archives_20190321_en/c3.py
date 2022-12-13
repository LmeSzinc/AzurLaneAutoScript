from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

from ..campaign_war_archives.campaign_base import CampaignBase
from .c1 import Config as ConfigBase

from module.map_detection.grid import Grid
from module.template.assets import TEMPLATE_FLEET_CURRENT

MAP = CampaignMap('C3')
MAP.shape = 'H7'
MAP.camera_data = ['D2', 'D5', 'E2', 'E5']
MAP.camera_data_spawn_point = ['C1']
MAP.map_data = """
    SP -- -- ++ ++ ++ ++ ++
    -- ++ Me -- ME -- -- ++
    SP -- -- Me ME -- ME ++
    ++ ++ ++ ++ ++ ME -- ++
    ++ MB ME ++ ++ -- ME --
    ++ ME ME ME ME Me ++ --
    ++ ME -- ME Me -- ME --
"""
MAP.weight_data = """
    50 50 50 50 50 50 50 50
    50 50 20 50 20 50 50 50
    50 50 50 30 20 50 50 50
    50 50 50 50 50 10 50 50
    50 10 10 50 50 10 50 50
    50 10 10 10 10 10 50 50
    50 50 50 50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 4},
    {'battle': 1, 'enemy': 1},
    {'battle': 2, 'enemy': 1},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'enemy': 1},
    {'battle': 6, 'boss': 1},
]
A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
A6, B6, C6, D6, E6, F6, G6, H6, \
A7, B7, C7, D7, E7, F7, G7, H7, \
    = MAP.flatten()

class EventGrid(Grid):
    def predict_current_fleet(self):
        count = self.relative_hsv_count(area=(-0.5, -3.5, 0.5, -2.5), h=(141 - 3, 141 + 10), shape=(50, 50))
        if count < 200:
            return False

        # image = self.relative_crop((-0.5, -3.5, 0.5, -2.5), shape=(60, 60))
        # image = color_similarity_2d(image, color=(24, 255, 107))
        # if not TEMPLATE_FLEET_CURRENT.match(image, similarity=0.75):
        #     return False

        return True

class Config(ConfigBase):
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = True
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = True
    MAP_HAS_MYSTERY = False
    # ===== End of generated config =====


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        if self.fleet_2_push_forward():
            return True

        return self.battle_default()

    def battle_6(self):
        return self.fleet_boss.clear_boss()
