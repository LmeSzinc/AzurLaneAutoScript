from module.base.mask import Mask
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.map_detection.utils_assets import ASSETS

MASK_MAP_UI_20211125 = Mask(file='./assets/mask/MASK_MAP_UI_20211125.png')


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        'T1 > T2 > T3 > T4',
        'TSS1 > TSS2 > TSS3 > TSS4 > TSS5',
    ]

    def map_data_init(self, map_):
        super().map_data_init(map_)
        # Patch ui_mask, get rid of map mechanism
        _ = ASSETS.ui_mask
        ASSETS.ui_mask = MASK_MAP_UI_20211125.image

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
        if name == 'tss':
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
        if 'sss' in name:
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
                if 'sss' in stage_name.lower():
                    name = stage_name

        return super().campaign_get_entrance(name)
