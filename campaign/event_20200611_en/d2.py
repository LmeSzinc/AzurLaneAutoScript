from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger
from campaign.event_20200521_cn.d1 import Config as ConfigBase


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
