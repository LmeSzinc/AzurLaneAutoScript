from module.base.button import Button
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.exception import CampaignNameError
from module.logger import logger

EVENT_ANIMATION = Button(area=(49, 229, 119, 400), color=(118, 215, 240), button=(49, 229, 119, 400),
                         name='EVENT_ANIMATION')


class CampaignBase(CampaignBase_):
    """
    In event Vacation Lane (event_20201126_cn), DOA collaboration, maps are:
    Chapter 1: SP1, SP2, SP3, SP4.
    Chapter 2: VSP.
    Chapter 3: EX.
    Mode switch is meaningless.
    """

    @staticmethod
    def _campaign_separate_name(name):
        """
        Args:
            name (str): Stage name in lowercase, such as 7-2, d3, sp3.

        Returns:
            tuple[str]: Campaign_name and stage index in lowercase, Such as ['7', '2'], ['d', '3'], ['sp', '3'].
        """
        if name == 'vsp' or name == 'sp':  # Difference
            return 'ex_sp', '1'
        return CampaignBase_._campaign_separate_name(name)

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
            elif name in ['ex_ex']:  # Difference
                return 3
            else:
                raise CampaignNameError

    def campaign_set_chapter_event(self, chapter, mode='normal'):
        self.ui_goto_event()
        self.campaign_ensure_chapter(chapter)
        return True

    def campaign_get_entrance(self, name):
        if name == 'sp':
            name = 'vsp'
        return super().campaign_get_entrance(name)

    def is_event_animation(self):
        """
        Animation in events after cleared an enemy.

        Returns:
            bool: If animation appearing.
        """
        appear = self.appear(EVENT_ANIMATION)
        if appear:
            logger.info('DOA animation, waiting')
        return appear
