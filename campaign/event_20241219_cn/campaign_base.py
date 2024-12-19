from campaign.event_20241024_cn.campaign_base import CHAPTER_SWITCH_20241024, MODE_SWITCH_20240725
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger


class CampaignBase(CampaignBase_):
    def campaign_ensure_mode(self, mode='normal'):
        """
        Args:
            mode (str): 'normal', 'hard', 'ex', 'story'

        Returns:
            bool: If mode changed.
        """
        if mode == 'hard':
            self.config.override(Campaign_Mode='hard')

        if mode in ['normal', 'hard', 'ex']:
            MODE_SWITCH_20240725.set('combat', main=self)
        elif mode in ['story']:
            MODE_SWITCH_20240725.set('story', main=self)
        else:
            logger.warning(f'Unknown campaign mode: {mode}')

    def campaign_set_chapter(self, name, mode='normal'):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
        """
        chapter, stage = self._campaign_separate_name(name)
        logger.info([chapter, stage])

        if chapter in ['a', 'c']:
            self.ui_goto_event()
            MODE_SWITCH_20240725.set('combat', main=self)
            if stage in ['1', '2', '3']:
                CHAPTER_SWITCH_20241024.set('ab', main=self)
            else:
                logger.warning(f'Stage {name} is not in CHAPTER_SWITCH_20241024')
            self.campaign_set_chapter_event(chapter, mode=mode)
        elif chapter in ['b', 'd']:
            self.ui_goto_event()
            MODE_SWITCH_20240725.set('combat', main=self)
            if stage in ['1', '2', '3']:
                CHAPTER_SWITCH_20241024.set('cd', main=self)
            else:
                logger.warning(f'Stage {name} is not in CHAPTER_SWITCH_20241024')
            self.campaign_set_chapter_event(chapter, mode=mode)
        elif chapter in ['ex_sp']:
            self.ui_goto_event()
            MODE_SWITCH_20240725.set('combat', main=self)
            CHAPTER_SWITCH_20241024.set('sp', main=self)
            self.campaign_set_chapter_event(chapter, mode=mode)
        elif chapter in ['ex_ex']:
            self.ui_goto_event()
            MODE_SWITCH_20240725.set('combat', main=self)
            CHAPTER_SWITCH_20241024.set('ex', main=self)
            self.campaign_set_chapter_event(chapter, mode=mode)
        else:
            logger.warning(f'Unknown campaign chapter: {name}')
