from campaign.event_20200611_en.d1 import Config as ConfigBase
from module.campaign.campaign_base import CampaignBase
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

MAP = CampaignMap()
MAP.map_data = """
    -- -- -- -- ++ -- -- -- -- ++ ++
    -- -- -- -- -- -- ++ ++ -- -- --
    ++ -- -- -- -- -- ++ ++ -- -- --
    -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- --
    ++ ++ -- -- -- -- ++ ++ -- -- --
    ++ -- -- -- -- -- -- -- -- -- --
"""
MAP.camera_data = ['D3', 'D5', 'F3', 'F5', 'H3', 'H5']
MAP.wall_data = """
    ·   · | ·   ·   ·   ·   ·   ·   ·   ·   · ,
          +                                   ,
    ·   ·   ·   ·   ·   ·   ·   ·   ·   · | · ,
          +       +   +               +   +   ,
    ·   · | ·   · | · | ·   ·   ·   · | ·   · ,
          +---+---+   |               |   +   ,
    ·   ·   · | ·   · | ·   ·   ·   · | · | · ,
              +---+   +---+       +---+   +-- ,
    ·   ·   ·   ·   ·   ·   ·   ·   ·   ·   · ,
                                              ,
    ·   ·   ·   ·   ·   ·   ·   ·   ·   ·   · ,
                                              ,
    ·   ·   ·   ·   ·   ·   ·   ·   ·   ·   · ,
"""


class Config(ConfigBase):
    MAP_HAS_WALL = True
    MAP_SIREN_TEMPLATE = ['Algerie', 'Vauquelin']


class Campaign(CampaignBase):
    MAP = MAP
