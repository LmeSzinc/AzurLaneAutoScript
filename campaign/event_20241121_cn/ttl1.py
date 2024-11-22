from module.config.config import AzurLaneConfig
from .campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger

MAP = CampaignMap('TTL1')
MAP.shape = 'E5'
MAP.camera_data = ['C2']
MAP.camera_data_spawn_point = ['C2']
MAP.map_data = """
    ++ ++ -- ++ ++
    ++ ++ MB ++ ++
    -- -- -- -- --
    ++ -- SP -- ++
    -- ++ ++ ++ --
"""
MAP.weight_data = """
    50 50 50 50 50
    50 50 50 50 50
    50 50 50 50 50
    50 50 50 50 50
    50 50 50 50 50
"""
MAP.spawn_data = [
    {'battle': 0, 'boss': 1},
]
A1, B1, C1, D1, E1, \
A2, B2, C2, D2, E2, \
A3, B3, C3, D3, E3, \
A4, B4, C4, D4, E4, \
A5, B5, C5, D5, E5, \
    = MAP.flatten()


class Config:
    # ===== Start of generated config =====
    MAP_HAS_MAP_STORY = False
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_AMBUSH = False
    MAP_HAS_MYSTERY = False
    STAR_REQUIRE_1 = 0
    STAR_REQUIRE_2 = 0
    STAR_REQUIRE_3 = 0
    # ===== End of generated config =====

    STAGE_ENTRANCE = ['half', '20240725']
    MAP_IS_ONE_TIME_STAGE = True
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 33),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 33, 255),
        'prominence': 10,
        'distance': 50,
        # 'width': (0, 7),
        'wlen': 1000
    }
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    MAP_SWIPE_MULTIPLY = (1.107, 1.128)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.071, 1.091)
    MAP_SWIPE_MULTIPLY_MAATOUCH = (1.040, 1.059)


class Campaign(CampaignBase):
    MAP = MAP
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        return self.clear_boss()


if __name__ == '__main__':
    cfg = AzurLaneConfig('alas5').merge(Config())
    self = Campaign(cfg)
    self.device.screenshot()
    self.campaign_set_chapter('ttl1', 'normal')
    self.ENTRANCE = self.campaign_get_entrance(name='ttl1')