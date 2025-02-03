from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.ui.page import page_event


class CampaignBase(CampaignBase_):
    def handle_clear_mode_config_cover(self):
        if super().handle_clear_mode_config_cover():
            self.config.MAP_SIREN_TEMPLATE = ['SS']
            self.config.MAP_HAS_SIREN = True

    def handle_exp_info(self):
        # Random background hits EXP_INFO_B
        if self.ui_page_appear(page_event):
            return False
        return super().handle_exp_info()
