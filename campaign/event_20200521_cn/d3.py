from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger
from campaign.event_20200521_cn.d1 import Config as ConfigBase


MAP = CampaignMap()
MAP.map_data = """
    -- -- -- -- -- -- -- -- -- -- -- -- -- ++
    -- -- -- -- -- -- -- -- -- -- -- -- -- --
    ++ -- -- -- -- -- -- -- -- -- -- -- -- --
    ++ -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- ++ ++
    -- ++ -- -- ++ ++ -- -- ++ ++ -- -- -- --
    -- ++ -- -- ++ ++ -- -- ++ ++ -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- ++ ++
    ++ -- -- -- -- -- -- -- -- -- -- -- ++ ++
    -- -- -- -- -- -- -- -- -- -- -- -- -- --
"""
MAP.camera_data = ['G8', 'G6', 'F3', 'I3']
MAP.wall_data = """
    ·   ·   ·   ·   · | ·   ·   ·   · | ·   ·   ·   ·   · ,
          +-----------+               +-----------+       ,
    ·   · | ·   ·   · | ·   ·   ·   · | ·   ·   · | ·   · ,
          |           |               |           |       ,
    ·   · | ·   ·   · | ·   ·   ·   · | ·   ·   · | ·   · ,
          +---+       +---+       +----+       +---+       ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |           ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |           ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |            ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |           ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              |                               |           ,
    ·   ·   · | ·   ·   ·   ·   ·   ·   ·   · | ·   ·   · ,
              +-----------+       +-----------+           ,
    ·   ·   ·   ·   ·   · | ·   · | ·   ·   ·   ·   ·   · ,
"""


class Config(ConfigBase):
    MAP_HAS_WALL = True
    MAP_SIREN_TEMPLATE = ['LaGalissonniere', 'Vauquelin']


class Campaign(CampaignBase):
    MAP = MAP
