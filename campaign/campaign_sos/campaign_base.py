from module.base.button import Button
from module.base.utils import *
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.exception import CampaignNameError
from module.template.assets import TEMPLATE_STAGE_SOS


class CampaignBase(CampaignBase_):
    ENEMY_FILTER = '1T > 1L > 1E > 1M > 2T > 2L > 2E > 2M > 3T > 3L > 3E > 3M'

    def campaign_get_entrance(self, name):
        """
        SOS stages don't have names in game, although players call them X-5 or X-sos.
        In most stages, alas use ocr to find stage entrances, but here, consider the submarine icon as stage entrance.

        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.

        Returns:
            Button:
        """
        if '-5' not in name:
            return super().campaign_get_entrance(name)

        sim, button = TEMPLATE_STAGE_SOS.match_result(self.device.image)
        if sim < 0.85:
            raise CampaignNameError

        entrance = button.crop((-12, -12, 44, 32), image=self.device.image, name=name)
        return entrance
