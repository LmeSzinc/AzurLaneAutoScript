from module.campaign.assets import *
from module.campaign.campaign_ocr import CampaignOcr
from module.exception import CampaignNameError, ScriptEnd
from module.logger import logger
from module.ui.switch import Switch
from module.ui.ui import UI, page_campaign, page_event, page_sp

STAGE_SHOWN_WAIT = (1, 1.2)
MODE_SWITCH_1 = Switch('Mode_switch_1', offset=(30, 10))
MODE_SWITCH_1.add_status('normal', SWITCH_1_NORMAL, sleep=STAGE_SHOWN_WAIT)
MODE_SWITCH_1.add_status('hard', SWITCH_1_HARD, sleep=STAGE_SHOWN_WAIT)
MODE_SWITCH_2 = Switch('Mode_switch_2', offset=(30, 10))
MODE_SWITCH_2.add_status('hard', SWITCH_2_HARD, sleep=STAGE_SHOWN_WAIT)
MODE_SWITCH_2.add_status('ex', SWITCH_2_EX, sleep=STAGE_SHOWN_WAIT)


class CampaignUI(UI, CampaignOcr):
    ENTRANCE = Button(area=(), color=(), button=(), name='default_button')

    def campaign_ensure_chapter(self, index):
        """
        Args:
            index (int, str): Chapter. Such as 7, 'd', 'sp'.
        """
        index = self._campaign_get_chapter_index(index)

        # A tricky way to use ui_ensure_index.
        self.ui_ensure_index(index, letter=self.get_chapter_index,
                             prev_button=CHAPTER_PREV, next_button=CHAPTER_NEXT,
                             fast=True, skip_first_screenshot=True, step_sleep=STAGE_SHOWN_WAIT, finish_sleep=0)

    def campaign_ensure_mode(self, mode='normal'):
        """
        Args:
            mode (str): 'normal', 'hard', 'ex'

        Returns:
            bool: If mode changed.
        """
        switch_2 = MODE_SWITCH_2.get(main=self)

        if switch_2 == 'unknown':
            if mode == 'ex':
                logger.warning('Trying to goto EX, but no EX mode switch')
            elif mode == 'normal':
                MODE_SWITCH_1.set('hard', main=self)
            elif mode == 'hard':
                MODE_SWITCH_1.set('normal', main=self)
            else:
                logger.warning(f'Unknown campaign mode: {mode}')
        else:
            if mode == 'ex':
                MODE_SWITCH_2.set('hard', main=self)
            elif mode == 'normal':
                MODE_SWITCH_2.set('ex', main=self)
                MODE_SWITCH_1.set('hard', main=self)
            elif mode == 'hard':
                MODE_SWITCH_2.set('ex', main=self)
                MODE_SWITCH_1.set('normal', main=self)
            else:
                logger.warning(f'Unknown campaign mode: {mode}')

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

        entrance = self.stage_entrance[name]
        entrance.name = name
        return entrance

    def campaign_set_chapter(self, name, mode='normal'):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
        """
        chapter, _ = self._campaign_separate_name(name)

        if chapter.isdigit():
            self.ui_goto(page_campaign)
            self.campaign_ensure_mode('normal')
            self.campaign_ensure_chapter(index=chapter)
            if mode == 'hard':
                self.campaign_ensure_mode('hard')
                self.campaign_ensure_chapter(index=chapter)

        elif chapter in ['a', 'b', 'c', 'd', 'ex_sp', 'as', 'bs', 'cs', 'ds']:
            self.ui_goto_event()
            if chapter in ['a', 'b', 'as', 'bs']:
                self.campaign_ensure_mode('normal')
            elif chapter in ['c', 'd', 'cs', 'ds']:
                self.campaign_ensure_mode('hard')
            elif chapter == 'ex_sp':
                self.campaign_ensure_mode('ex')
            self.campaign_ensure_chapter(index=chapter)

        elif chapter == 'sp':
            self.ui_goto_sp()
            self.campaign_ensure_chapter(index=chapter)

        else:
            logger.warning(f'Unknown campaign chapter: {name}')

    def ensure_campaign_ui(self, name, mode='normal'):
        for n in range(20):
            try:
                self.campaign_set_chapter(name, mode)
                self.ENTRANCE = self.campaign_get_entrance(name=name)
                return True
            except CampaignNameError:
                pass

            self.device.screenshot()

        logger.warning('Campaign name error')
        raise ScriptEnd('Campaign name error')

    def commission_notice_show_at_campaign(self):
        """
        Returns:
            bool: If any commission finished.
        """
        return self.appear(page_campaign.check_button, offset=(20, 20)) and self.appear(COMMISSION_NOTICE_AT_CAMPAIGN)
