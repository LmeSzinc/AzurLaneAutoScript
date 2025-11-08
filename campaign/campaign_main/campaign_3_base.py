from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger
from module.ui.page import page_campaign


class CampaignBase(CampaignBase_):
    def handle_exp_info(self):
        # Random background of Main Chapter 3 hits EXP_INFO_B
        if self.ui_page_appear(page_campaign):
            return False
        return super().handle_exp_info()
