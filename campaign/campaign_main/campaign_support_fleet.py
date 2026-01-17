from module.base.mask import Mask
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger
from module.map.assets import FLEET_SUPPORT_EMPTY
from module.map_detection.utils_assets import ASSETS

MASK_MAP_UI_SUPPORT = Mask(file='./assets/mask/MASK_MAP_UI_SUPPORT.png')


class CampaignBase(CampaignBase_):
    use_support_fleet = True

    def fleet_preparation(self):
        if self.appear(FLEET_SUPPORT_EMPTY, offset=(5, 5)):
            self.use_support_fleet = False
        logger.attr("use_support_fleet", self.use_support_fleet)
        super().fleet_preparation()

    def _map_swipe(self, vector, box=(239, 159, 1175, 628)):
        # Left border to 239, avoid swiping on support fleet
        return super()._map_swipe(vector, box=box)

    def map_data_init(self, map_):
        super().map_data_init(map_)
        if self.use_support_fleet:
            # Patch ui_mask, get rid of supporting fleet
            _ = ASSETS.ui_mask
            ASSETS.ui_mask = MASK_MAP_UI_SUPPORT.image
