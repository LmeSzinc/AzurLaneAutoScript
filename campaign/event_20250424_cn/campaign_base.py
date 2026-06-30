from module.campaign.assets import EVENT_20250424_PT_ICON
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger
from module.ui.page import page_campaign_menu, page_event


class CampaignBase(CampaignBase_):
    def handle_exp_info(self):
        # Random background of hits EXP_INFO_B
        if self.ui_page_appear(page_event):
            return False
        return super().handle_exp_info()

    def ui_goto_event(self):
        if self.appear(EVENT_20250424_PT_ICON, offset=(20, 20)) and self.ui_page_appear(page_event):
            logger.info('Already at EVENT_20250424')
            return True
        self.ui_ensure(page_campaign_menu)
        if self.is_event_entrance_available():
            self.ui_goto(page_event)
            return True
