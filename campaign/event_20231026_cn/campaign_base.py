from module.base.utils import color_similarity_2d
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.map_detection.grid import Grid
from module.template.assets import TEMPLATE_ENEMY_BOSS


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        """
        T1 > T2 > T3 > T4 > T5 > T6
        """
    ]

    def campaign_set_chapter_event(self, chapter, mode='normal'):
        self.ui_goto_event()
        self.campaign_ensure_chapter(index=chapter)
        return True

    def _campaign_get_chapter_index(self, name):
        """
        Args:
            name (str, int):

        Returns:
            int
        """
        if name == 't1':
            return 1
        if name == 't2':
            return 2
        if name == 'ex_sp':
            return 3
        if name == 'ex_ex':
            return 4

        return super(CampaignBase, CampaignBase)._campaign_get_chapter_index(name)

    @staticmethod
    def _campaign_separate_name(name):
        """
        Args:
            name (str): Stage name in lowercase, such as 7-2, d3, sp3.

        Returns:
            tuple[str]: Campaign_name and stage index in lowercase, Such as ['7', '2'], ['d', '3'], ['sp', '3'].
        """
        if name in ['t1', 't2', 't3']:
            return 't1', name[-1]
        if name in ['t4', 't5', 't6']:
            return 't2', name[-1]
        if 'esp' in name:
            return ['ex_sp', '1']
        if 'ex' in name:
            return ['ex_ex', '1']

        return super(CampaignBase, CampaignBase)._campaign_separate_name(name)
