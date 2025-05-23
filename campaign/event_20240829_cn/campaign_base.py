
from module.campaign.campaign_base import CampaignBase as CampaignBase_


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

        self.campaign_ensure_mode_20241219(mode)

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
