from campaign.event_20200611_en.b1 import Config as ConfigBase
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.shape = 'N10'
MAP.map_data = """
    -- -- -- -- -- ME -- -- ME -- -- -- -- ++
    -- -- -- ME -- -- MB MB -- -- ME -- -- --
    ++ -- ME -- ME ME -- -- ME ME -- ME -- --
    ++ -- -- ME -- -- __ __ -- -- ME -- -- --
    -- -- -- -- ME MS -- -- MS ME -- -- ++ ++
    -- ++ -- ME ++ ++ -- -- ++ ++ ME -- -- --
    -- ++ -- ME ++ ++ -- -- ++ ++ ME -- -- --
    -- -- -- -- ME MS -- -- MS ME -- -- ++ ++
    ++ -- -- -- -- -- -- -- -- -- -- -- ++ ++
    -- -- -- -- -- -- SP SP -- -- -- -- -- --
"""
MAP.camera_data = ['G8', 'G6', 'F3', 'H4']
MAP.wall_data = """
    ·   ·   ·   ·   · | ·   ·   ·   · | ·   ·   ·   ·   · ,
          +-----------+               +-----------+       ,
    ·   · | ·   ·   · | ·   ·   ·   · | ·   ·   · | ·   · ,
          |           |               |           |       ,
    ·   · | ·   ·   · | ·   ·   ·   · | ·   ·   · | ·   · ,
          +---+       +---+       +---+       +---+       ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |           ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |           ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |           ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |           ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |           ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              +-----------+       +-----------+           ,
    ·   ·   ·   ·   ·   · | ·   · | ·   ·   ·   ·   ·   · ,
"""
MAP.spawn_data = [
    {'battle': 0, 'enemy': 2, 'siren': 2},
    {'battle': 1, 'enemy': 2},
    {'battle': 2, 'enemy': 2},
    {'battle': 3, 'enemy': 1},
    {'battle': 4, 'enemy': 1},
    {'battle': 5, 'enemy': 1, 'boss': 1},
]


class Config(ConfigBase):
    MAP_SIREN_COUNT = 2
    MAP_HAS_WALL = True
    MAP_SIREN_TEMPLATE = ['LaGalissonniere', 'Vauquelin']

    EDGE_LINES_HOUGHLINES_THRESHOLD = 40


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

    def battle_5(self):
        return self.fleet_boss.brute_clear_boss()
