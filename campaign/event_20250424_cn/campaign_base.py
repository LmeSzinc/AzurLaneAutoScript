from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.campaign.campaign_ui import MODE_SWITCH_20241219, ASIDE_SWITCH_20241219


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

    def campaign_set_chapter_20241219(self, chapter, stage, mode='combat'):
        if chapter == 't':
            self.ui_goto_event()
            MODE_SWITCH_20241219.set('combat', main=self)
            ASIDE_SWITCH_20241219.set('part2', main=self)
            self.campaign_ensure_chapter(chapter)
        if chapter == 'ex_sp':
            self.ui_goto_event()
            MODE_SWITCH_20241219.set('combat', main=self)
            ASIDE_SWITCH_20241219.set('sp', main=self)
            self.campaign_ensure_chapter(chapter)
            return True

        return super().campaign_set_chapter_20241219(chapter, stage, mode)
