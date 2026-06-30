from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.ui.page import page_event


class CampaignBase(CampaignBase_):
    def handle_exp_info(self):
        # Random background of hits EXP_INFO_B
        if self.ui_page_appear(page_event):
            return False
        return super().handle_exp_info()

    def map_data_init(self, map_):
        super().map_data_init(map_)
        self.config.override(EnemyPriority_EnemyScaleBalanceWeight='default_mode')
