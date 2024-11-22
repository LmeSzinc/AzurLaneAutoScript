from campaign.event_20241024_cn.campaign_base import CHAPTER_SWITCH_20241024, MODE_SWITCH_20240725
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        'T1 > T2 > T3 > T4 > T5 > T6',
        'TTL1 > TTL2 > TTL3 > TTL4 > TTL5',
    ]

    @staticmethod
    def _campaign_get_chapter_index(name):
        """
        Args:
            name (str, int):

        Returns:
            int
        """
        if name == 'ttl':
            return 1
        return CampaignBase_._campaign_get_chapter_index(name)

    def campaign_set_chapter(self, name, mode='normal'):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
        """
        chapter, stage = self._campaign_separate_name(name)
        logger.info([chapter, stage])

        if chapter in ['t']:
            self.ui_goto_event()
            MODE_SWITCH_20240725.set('combat', main=self)
            if stage in ['1', '2', '3', '4', '5']:
                CHAPTER_SWITCH_20241024.set('ab', main=self)
            else:
                logger.warning(f'Stage {name} is not in CHAPTER_SWITCH_20241024')
            self.campaign_ensure_chapter(index=chapter)
        elif chapter in ['ttl']:
            self.ui_goto_event()
            MODE_SWITCH_20240725.set('combat', main=self)
            if stage in ['1', '2', '3', '4', '5']:
                CHAPTER_SWITCH_20241024.set('cd', main=self)
            else:
                logger.warning(f'Stage {name} is not in CHAPTER_SWITCH_20241024')
            logger.info('campaign_ensure_chapter')
            self.campaign_ensure_chapter(index=chapter)
        elif chapter in ['ex_sp']:
            self.ui_goto_event()
            MODE_SWITCH_20240725.set('combat', main=self)
            CHAPTER_SWITCH_20241024.set('sp', main=self)
            self.campaign_ensure_chapter(index=chapter)
        elif chapter in ['ex_ex']:
            self.ui_goto_event()
            MODE_SWITCH_20240725.set('combat', main=self)
            CHAPTER_SWITCH_20241024.set('ex', main=self)
            self.campaign_ensure_chapter(index=chapter)
        else:
            logger.warning(f'Unknown campaign chapter: {name}')
