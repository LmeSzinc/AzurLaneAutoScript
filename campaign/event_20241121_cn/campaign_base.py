from module.campaign.assets import *
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.campaign.campaign_ui import ModeSwitch
from module.logger import logger

MODE_SWITCH_20240725 = ModeSwitch('Mode_switch_20240725', is_selector=True, offset=(30, 30))
MODE_SWITCH_20240725.add_status('combat', SWITCH_20240725_COMBAT, offset=(444, 4))
MODE_SWITCH_20240725.add_status('story', SWITCH_20240725_STORY, offset=(444, 4))

CHAPTER_SWITCH_20241024 = ModeSwitch('Chapter_switch_20241024', is_selector=True, offset=(30, 30))
CHAPTER_SWITCH_20241024.add_status('ab', CHAPTER_20241024_AB)
CHAPTER_SWITCH_20241024.add_status('cd', CHAPTER_20241024_CD)
CHAPTER_SWITCH_20241024.add_status('sp', CHAPTER_20241024_SP)
CHAPTER_SWITCH_20241024.add_status('ex', CHAPTER_20241024_EX)

class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        """
        T1 > T2 > T3 > T4 > T5
        """,
        """
        TTL1 > TTL2 > TTL3 > TTL4 > TTL5
        """,
    ]

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

    def _campaign_get_chapter_index(self, name):
        """
        Args:
            name (str, int):

        Returns:
            int
        """
        if name == 't':
            return 1
        if name == 'ttl':
            return 2
        if name == 'ex_sp':
            return 3
        if name == 'ex_ex':
            return 4

        return super(CampaignBase, CampaignBase)._campaign_get_chapter_index(name)