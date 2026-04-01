from ..campaign_war_archives.campaign_base import CampaignBase as CampaignBase_
from module.ui.page import page_event


class CampaignBase(CampaignBase_):
    def handle_exp_info(self):
        # Random background of chapter A hits EXP_INFO_B
        if self.ui_page_appear(page_event):
            return False
        return super().handle_exp_info()
