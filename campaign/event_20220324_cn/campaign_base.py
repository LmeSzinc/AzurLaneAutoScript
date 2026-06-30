from module.campaign.campaign_base import CampaignBase as CampaignBase_


class CampaignBase(CampaignBase_):
    def campaign_set_chapter_sp(self, chapter, mode='normal'):
        if chapter == 'sp':
            self.ui_goto_event()
            self.campaign_ensure_chapter(chapter)
            return True
        else:
            return False

    def campaign_ensure_mode(self, mode='normal'):
        """
        Args:
            mode (str): 'normal', 'hard', 'ex'

        Returns:
            bool: If mode changed.
        """
        # No need to switch
        pass

    def _campaign_get_chapter_index(self, name):
        """
        Args:
            name (str, int):

        Returns:
            int
        """
        if name == 't':
            return 1
        if name == 'ex_sp':
            return 2
        if name == 'ex_ex':
            return 3

        return super(CampaignBase, CampaignBase)._campaign_get_chapter_index(name)

    @staticmethod
    def _campaign_separate_name(name):
        """
        Args:
            name (str): Stage name in lowercase, such as 7-2, d3, sp3.

        Returns:
            tuple[str]: Campaign_name and stage index in lowercase, Such as ['7', '2'], ['d', '3'], ['sp', '3'].
        """
        if 'esp' in name:
            return ['ex_sp', '1']
        if 'ex' in name:
            return ['ex_ex', '1']

        return super(CampaignBase, CampaignBase)._campaign_separate_name(name)

    def campaign_get_entrance(self, name):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.

        Returns:
            Button:
        """
        if name == 'sp':
            for stage_name, stage_obj in self.stage_entrance.items():
                if 'esp' in stage_name.lower():
                    name = stage_name

        return super().campaign_get_entrance(name)
