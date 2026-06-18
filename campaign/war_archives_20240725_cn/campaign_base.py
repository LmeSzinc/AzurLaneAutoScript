from ..campaign_war_archives.campaign_base import CampaignBase as CampaignBase_


class CampaignBase(CampaignBase_):
    def campaign_set_chapter_event(self, chapter, mode='normal'):
        self.ui_goto_sp()
        self.campaign_ensure_chapter(chapter)
        return True

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
