from module.base.utils import get_color, red_overlay_transparency
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.handler.assets import MAP_ENEMY_SEARCHING
from module.map.assets import SWITCH_OVER


class CampaignBase(CampaignBase_):
    def enemy_searching_appear(self):
        if not self.appear(SWITCH_OVER, offset=(20, 20)):
            return False

        return red_overlay_transparency(
            MAP_ENEMY_SEARCHING.color, get_color(self.device.image, MAP_ENEMY_SEARCHING.area)
        ) > self.MAP_ENEMY_SEARCHING_OVERLAY_TRANSPARENCY_THRESHOLD
