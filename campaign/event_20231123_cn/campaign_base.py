from module.campaign.campaign_base import CampaignBase as CampaignBase_


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        """
        T1 > T2 > T3 > T4 > T5
        """,
        """
        TSK1 > TSK2 > TSK3 > TSK4 > TSK5
        """,
    ]

    def campaign_set_chapter_event(self, chapter, mode='normal'):
        self.ui_goto_event()
        self.campaign_ensure_chapter(chapter)
        return True

    def _campaign_get_chapter_index(self, name):
        """
        Args:
            name (str, int):

        Returns:
            int
        """
        if name == 't':
            return 1
        if name == 'tsk':
            return 2
        if name == 'ex_sp':
            return 3
        if name == 'ex_ex':
            return 4

        return super(CampaignBase, CampaignBase)._campaign_get_chapter_index(name)
