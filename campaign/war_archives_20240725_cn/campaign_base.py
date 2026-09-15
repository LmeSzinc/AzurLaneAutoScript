from ..campaign_war_archives.campaign_base import CampaignBase as CampaignBase_


class CampaignBase(CampaignBase_):
    def campaign_set_chapter_event(self, chapter, mode='normal'):
        self.ui_goto_sp()
        if chapter in ['a', 'b', 'as', 'bs', 't', 'ts', 'tss']:
            self.campaign_ensure_mode('normal')
        elif chapter in ['c', 'd', 'cs', 'ds', 'ht', 'hts']:
            self.campaign_ensure_mode('hard')
        elif chapter == 'ex_sp':
            self.campaign_ensure_mode('ex')
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

        # this event only have chapter T/HT and chapter SP, and war archive does not have SP
        # so there is no mode switch buttons
        # self.campaign_ensure_mode_20241219(mode)
