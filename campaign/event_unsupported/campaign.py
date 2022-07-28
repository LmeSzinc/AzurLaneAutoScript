from module.map.map_base import CampaignMap
from module.campaign.campaign_base import CampaignBase

MAP = CampaignMap()


class Config:
    pass


class Campaign(CampaignBase):
    MAP = MAP
