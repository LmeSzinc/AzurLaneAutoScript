import numpy as np

from module.base.button import Button
from module.base.utils import get_color
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger

# Here manually type coordinates, because the ball appears in this event only.
BALL = Button(area=(589, 279, 685, 374), color=(), button=(589, 279, 685, 374))


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        'T1 > T2 > TS1 > T3',
        'T4 > T5 > TS2 > T6',
        'HT1 > HT2 > HTS1 > HT3',
        'HT4 > HT5 > HTS2 > HT6',
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
            self.campaign_ensure_chapter(chapter)
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
            self.campaign_ensure_chapter(chapter)

        elif chapter == 'sp':
            self.ui_goto_sp()
            self.campaign_ensure_chapter(chapter)

        elif chapter in ['t', 'ts', 'ht', 'hts']:
            self.ui_goto_event()
            # Campaign mode
            if chapter in ['t', 'ts']:
                self.campaign_ensure_mode('normal')
            if chapter in ['ht', 'hts']:
                self.campaign_ensure_mode('hard')
            if chapter == 'ex_sp':
                self.campaign_ensure_mode('ex')
            if chapter in ['t', 'ht']:
                # Campaign ball
                if stage in ['1', '2', '3']:
                    self._campaign_ball_set('blue')
                else:
                    self._campaign_ball_set('red')
            elif chapter in ['ts', 'hts']:
                if stage in ['1']:
                    self._campaign_ball_set('blue')
                else:
                    self._campaign_ball_set('red')
            # Get stage
            self.campaign_ensure_chapter(1)
        else:
            logger.warning(f'Unknown campaign chapter: {name}')

    def _campaign_ball_get(self):
        """
        Returns:
            str: 'blue' or 'red'.
        """
        color = get_color(self.device.image, BALL.area)
        # Blue: (93, 127, 182), Red: (186, 116, 124)
        index = np.argmax(color)
        if index == 0:
            return 'red'
        elif index == 2:
            return 'blue'
        else:
            logger.warning(f'Unknown campaign ball color: {color}')
            return 'unknown'

    def _campaign_ball_set(self, status):
        """
        Args:
            status (str): 'blue' or 'red'.
        """
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            current = self._campaign_ball_get()
            logger.attr('Campaign_ball', current)

            if current == status:
                break

            if self.is_in_stage():
                self.device.click(BALL)
                self.device.sleep(3)
                # wait until is_in_stage
                while 1:
                    self.device.screenshot()
                    if self.is_in_stage():
                        break
