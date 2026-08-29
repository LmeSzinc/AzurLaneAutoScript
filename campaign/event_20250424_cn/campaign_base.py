from module.campaign.assets import EVENT_20250424_PT_ICON
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.ui.page import page_event


class CampaignBase(CampaignBase_):
    def handle_exp_info(self):
        # Random background of hits EXP_INFO_B
        if self.ui_page_appear(page_event):
            return False
        return super().handle_exp_info()

    def ui_goto_event(self):
        if self.event_entrance_ensure(EVENT_20250424_PT_ICON, log_name='EVENT_20250424'):
            self.ui_goto(page_event)
            return True
