from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger


class CampaignBase(CampaignBase_):
    def campaign_set_chapter(self, name, mode='normal'):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
        """
        chapter, stage = self._campaign_separate_name(name)
        name = chapter + stage

        if chapter.isdigit():
            self.ui_weigh_anchor()
            self.campaign_ensure_mode('normal')
            self.campaign_ensure_chapter(index=chapter)
            if mode == 'hard':
                self.campaign_ensure_mode('hard')

        elif chapter in 'abcd' or chapter == 'ex_sp':
            self.ui_goto_event()
            if chapter in 'ab':
                self.campaign_ensure_mode('normal')
            elif chapter in 'cd':
                self.campaign_ensure_mode('hard')
            elif chapter == 'ex_sp':
                self.campaign_ensure_mode('ex')
            self.campaign_ensure_chapter(index=chapter)

        elif chapter == 'sp':
            self.ui_goto_sp()
            self.campaign_ensure_chapter(index=chapter)

        elif chapter in ['t', 'ts', 'ht']:
            self.ui_goto_event()
            if name == 'ts1' or chapter == 't':
                self.campaign_ensure_mode('normal')
            if name == 'ts2' or chapter == 'ht':
                self.campaign_ensure_mode('normal')
            if chapter == 'hts':
                self.campaign_ensure_mode('ex')
            self.campaign_ensure_chapter(index=1)
        else:
            logger.warning(f'Unknown campaign chapter: {name}')

    @staticmethod
    def _campaign_get_chapter_index(name):
        """
        Args:
            name (str, int):

        Returns:
            int
        """
        if isinstance(name, int):
            return name
        else:
            if name.isdigit():
                return int(name)
            elif name in ['a', 'c', 'sp', 'ex_sp', 'ts', 't', 'hts']:
                return 1
            elif name in ['b', 'd']:
                return 2
