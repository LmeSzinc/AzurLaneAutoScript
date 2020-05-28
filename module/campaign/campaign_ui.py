import numpy as np

from module.base.utils import get_color
from module.campaign.assets import *
from module.campaign.campaign_ocr import CampaignOcr, ensure_chapter_index, separate_name
from module.logger import logger
from module.ui.ui import UI
from module.exception import CampaignNameError

STAGE_SHOWN_WAIT = (1, 1.2)


class CampaignUI(UI, CampaignOcr):
    def campaign_ensure_chapter(self, index):
        """
        Args:
            index (int, str): Chapter. Such as 7, 'd', 'sp'.
        """
        index = ensure_chapter_index(index)

        # A tricky way to use ui_ensure_index.
        self.ui_ensure_index(index, letter=self.get_chapter_index,
                             prev_button=CHAPTER_PREV, next_button=CHAPTER_NEXT,
                             fast=True, skip_first_screenshot=True, step_sleep=STAGE_SHOWN_WAIT, finish_sleep=0)

    def campaign_predict_mode(self):
        """
        Returns:
            str: 'normal' or 'hard'
        """
        color = get_color(self.device.image, MODE_CHANGE.area)
        if np.max(color) - np.min(color) < 50:
            logger.warning(f'Unexpected color: {color}')
        index = np.argmax(color)  # R, G, B
        if index == 0:
            return 'normal'  # Red button. (214, 117, 115)
        elif index == 2:
            return 'hard'  # Blue button. (115, 146, 214)
        else:
            logger.warning(f'Unexpected color: {color}')

    def campaign_ensure_mode(self, mode='normal'):
        """
        Args:
            mode (str): 'normal', 'hard'.

        Returns:
            bool: If mode changed.
        """
        if self.campaign_predict_mode() == mode:
            return False
        else:
            # Poor click. May unstable.
            self.device.click(MODE_CHANGE)
            self.handle_stage_icon_spawn()
            return True

    def campaign_get_entrance(self, name):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.

        Returns:
            Button:
        """
        if name not in self.stage_entrance:
            logger.warning(f'Stage not found: {name}')
            raise CampaignNameError
        return self.stage_entrance[name]

    def ensure_campaign_ui(self, name, mode='normal'):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
        """
        chapter, _ = separate_name(name)

        if chapter.isdigit():
            self.ui_weigh_anchor()
            self.campaign_ensure_mode('normal')
            self.campaign_ensure_chapter(index=chapter)
            if mode == 'hard':
                self.campaign_ensure_mode('hard')

        elif chapter in 'abcd':
            self.ui_goto_event()
            if chapter in 'ab':
                self.campaign_ensure_mode('normal')
            else:
                self.campaign_ensure_mode('hard')
            self.campaign_ensure_chapter(index=chapter)

        elif chapter == 'sp':
            self.ui_goto_sp()
            self.campaign_ensure_chapter(index=chapter)
