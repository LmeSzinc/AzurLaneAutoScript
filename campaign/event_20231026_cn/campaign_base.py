import numpy as np
from module.campaign.assets import SWITCH_1_NORMAL
from module.base.button import Button
from module.base.utils import get_color
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger
from module.campaign.assets import CHAPTER_NEXT, CHAPTER_PREV


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        'T1 > T2 > T3',
        'T4 > T5 > T6',
    ]

    def campaign_set_chapter(self, name, mode='normal'):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
        """
        chapter, stage = self._campaign_separate_name(name)
        name = chapter + stage

        if chapter.isdigit():
            self.ui_goto_campaign()
            self.campaign_ensure_mode('normal')
            self.campaign_ensure_chapter(index=chapter)
            if mode == 'hard':
                self.campaign_ensure_mode('hard')

        elif chapter in 'abcd' or chapter == 'ex_sp':
            self.ui_goto_event()
            if chapter in 'ab':
                self.campaign_ensure_mode('normal')
            elif chapter in 'cd':
                self.campaign_ensure_mode('hard')
            elif chapter == 'ex_sp':
                self.campaign_ensure_mode('ex')
            self.campaign_ensure_chapter(index=chapter)

        elif chapter in ['t', 'ts', 'ht', 'hts']:
            self.ui_goto_event()
            self._get_stage_name(self.device.screenshot())
            current_stage = list(self.stage_entrance.keys())
            if chapter in ['t', 'ht']:
                if stage in ["1", "2", "3"] and "t4" in current_stage:
                    self.device.click(CHAPTER_PREV)
                elif stage in ["4", "5", "6"] and "t1" in current_stage:
                    self.device.click(CHAPTER_NEXT)
                elif current_stage[0] == "sp":
                    if stage in ["4", "5", "6"]:
                        self.device.click(SWITCH_1_NORMAL)
                    elif stage in ["1", "2", "3"]:
                        self.device.click(SWITCH_1_NORMAL)
                        self.device.sleep(0.5)
                        self.device.click(CHAPTER_PREV)
            # Get stage
            # self.campaign_ensure_chapter(index=1)
        else:
            logger.warning(f'Unknown campaign chapter: {name}')
