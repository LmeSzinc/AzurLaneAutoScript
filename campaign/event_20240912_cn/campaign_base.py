from module.campaign.assets import SWITCH_20240725_COMBAT, SWITCH_20240725_STORY
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.campaign.campaign_ui import ModeSwitch
from module.ui.ui import page_event


MODE_SWITCH_20240912 = ModeSwitch('Mode_switch_20240912', is_selector=True, offset=(30, 30))
MODE_SWITCH_20240912.add_status('combat', SWITCH_20240725_COMBAT, offset=(444, 4))
MODE_SWITCH_20240912.add_status('story', SWITCH_20240725_STORY, offset=(444, 4))


class CampaignBase(CampaignBase_):
    def campaign_ensure_mode(self, mode='normal'):
        """
        Args:
            mode (str): 'normal', 'hard', 'ex', 'story'

        Returns:
            bool: If mode changed.
        """
        if mode == "story":
            MODE_SWITCH_20240912.set('story', main=self)
        elif mode in ['normal', 'hard', 'ex']:
            # First switch to combat mode and then select Hard or Normal.
            MODE_SWITCH_20240912.set('combat', main=self)
            super().campaign_ensure_mode(mode)

    def handle_exp_info(self):
        # Random background of hits EXP_INFO_B
        if self.ui_page_appear(page_event):
            return False
        return super().handle_exp_info()
