from module.campaign.assets import SWITCH_20240725_COMBAT, SWITCH_20240725_STORY
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.campaign.campaign_ui import ModeSwitch
from module.logger import logger

MODE_SWITCH_20240725 = ModeSwitch('Mode_switch_20240725', offset=(30, 30))
MODE_SWITCH_20240725.add_status('combat', SWITCH_20240725_COMBAT)
MODE_SWITCH_20240725.add_status('story', SWITCH_20240725_STORY)


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

    @staticmethod
    def _campaign_separate_name(name):
        """
        Args:
            name (str): Stage name in lowercase, such as 7-2, d3, sp3.

        Returns:
            tuple[str]: Campaign_name and stage index in lowercase, Such as ['7', '2'], ['d', '3'], ['sp', '3'].
        """
        if name == 'tp':
            return 'ex_sp', '1'
        return CampaignBase_._campaign_separate_name(name)

    def campaign_get_entrance(self, name):
        if name == 'sp':
            name = 'tp'
        return super().campaign_get_entrance(name)
