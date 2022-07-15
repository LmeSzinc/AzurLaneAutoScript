from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.exception import CampaignNameError
from module.logger import logger


class CampaignBase(CampaignBase_):
    """
    In event Universe in Unison (event_20201029_cn), maps are:
    Chapter 1: SP1, SP2, SP3, SP4, SP5.
    Chapter 2: uSP.
    Chapter 3: EX.
    Mode switch is meaningless.
    """

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
            elif name in ['a', 'c', 'sp']:
                return 1
            elif name in ['b', 'd', 'ex_sp']:  # Difference
                return 2
            else:
                raise CampaignNameError

    def campaign_set_chapter(self, name, mode='normal'):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
        """
        chapter, stage = self._campaign_separate_name(name)

        if chapter.isdigit():
            self.ui_goto_campaign()
            self.campaign_ensure_mode('normal')
            self.campaign_ensure_chapter(index=chapter)
            if mode == 'hard':
                self.campaign_ensure_mode('hard')
                self.campaign_ensure_chapter(index=chapter)

        elif chapter in 'abcd' or chapter == 'ex_sp':
            self.ui_goto_event()
            if chapter in 'ab':
                self.campaign_ensure_mode('normal')
            elif chapter in 'cd':
                self.campaign_ensure_mode('hard')
            elif chapter == 'ex_sp':
                pass  # Difference
            self.campaign_ensure_chapter(index=chapter)

        elif chapter == 'sp':
            self.ui_goto_event()  # Difference
            self.campaign_ensure_chapter(index=chapter)

        else:
            logger.warning(f'Unknown campaign chapter: {name}')

    def is_event_animation(self):
        appear = self.image_color_count((286, 342, 994, 422), color=(255, 255, 255), count=10000)
        if appear:
            logger.info('Live start!')

        return appear
