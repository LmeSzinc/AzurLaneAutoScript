from module.exception import CampaignNameError
from module.logger import logger

from ..campaign_war_archives.campaign_base import CampaignBase as CampaignBase_


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        'A1 > AS1 > A2 > AS2 > A3',
        'B1 > B2 > B3',
        'C1 > CS1 > C2 > CS2 > C3',
        'D1 > D2 > D3',
        'SP1 > SP2 > SP3 > SP4',
        'T1 > T2 > T3 > T4',
    ]

    def campaign_set_chapter(self, name, mode='normal'):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
        """
        chapter, _ = self._campaign_separate_name(name)

        if chapter.isdigit():
            self.ui_goto_campaign()
            self.campaign_ensure_mode('normal')
            self.campaign_ensure_chapter(chapter)
            if mode == 'hard':
                self.campaign_ensure_mode('hard')
                self.campaign_ensure_chapter(chapter)

        elif chapter in 'abcd' or chapter == 'ex_sp' or chapter in ['as', 'cs']:
            self.ui_goto_event()
            if chapter in 'ab' or chapter == 'as':
                self.campaign_ensure_mode('normal')
            elif chapter in 'cd' or chapter == 'cs':
                self.campaign_ensure_mode('hard')
            elif chapter == 'ex_sp':
                self.campaign_ensure_mode('ex')
            self.campaign_ensure_chapter(chapter)

        elif chapter == 'sp':
            self.ui_goto_sp()
            self.campaign_ensure_chapter(chapter)

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
            elif name in ['a', 'c', 'sp', 'ex_sp', 'as', 'cs']:
                return 1
            elif name in ['b', 'd', 'ex_ex']:
                return 2
            else:
                raise CampaignNameError
