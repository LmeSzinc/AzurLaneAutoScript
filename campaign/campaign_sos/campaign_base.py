from module.base.button import Button
from module.base.utils import *
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.exception import CampaignNameError
from module.template.assets import TEMPLATE_STAGE_SOS


class CampaignBase(CampaignBase_):
    def campaign_get_entrance(self, name):
        """
        SOS stages don't have names in game, although players call them X-5 or X-sos.
        In most stages, alas use ocr to find stage entrances, but here, consider the submarine icon as stage entrance.

        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.

        Returns:
            Button:
        """
        sim, point = TEMPLATE_STAGE_SOS.match_result(self.device.image)
        if sim < 0.85:
            raise CampaignNameError

        button = area_offset(area=(-12, -12, 44, 32), offset=point)
        color = get_color(self.device.image, button)
        entrance = Button(area=button, color=color, button=button, name=name)
        return entrance
