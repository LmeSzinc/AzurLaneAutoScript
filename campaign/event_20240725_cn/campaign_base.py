from module.campaign.assets import SWITCH_20240725_COMBAT, SWITCH_20240725_STORY
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.campaign.campaign_ui import ModeSwitch
from module.logger import logger

MODE_SWITCH_20240725 = ModeSwitch('Mode_switch_20240725', offset=(30, 30))
MODE_SWITCH_20240725.add_state('combat', SWITCH_20240725_COMBAT)
MODE_SWITCH_20240725.add_state('story', SWITCH_20240725_STORY)


class CampaignBase(CampaignBase_):
    def campaign_ensure_mode(self, mode='normal'):
        """
        Args:
            mode (str): 'normal', 'hard', 'ex', 'story'

        Returns:
            bool: If mode changed.
        """
        if mode == 'hard':
            self.config.override(Campaign_Mode='hard')

        if mode in ['normal', 'hard', 'ex']:
            MODE_SWITCH_20240725.set('combat', main=self)
        elif mode in ['story']:
            MODE_SWITCH_20240725.set('story', main=self)
        else:
            logger.warning(f'Unknown campaign mode: {mode}')
