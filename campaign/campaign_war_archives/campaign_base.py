from module.base.utils import *
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.exception import CampaignNameError, ScriptEnd
from module.base.button import Button
from module.war_archives.assets import WAR_ARCHIVES_EX_OFF, WAR_ARCHIVES_SP_OFF, WAR_ARCHIVES_CAMPAIGN_CHECK
from module.ui.assets import WAR_ARCHIVES_CHECK
from module.ui.page import page_main, page_archives
from module.logger import logger
from module.config.dictionary import dic_archives_template
import module.config.server as server


class CampaignBase(CampaignBase_):
    # Helper to determine whether this is the first run
    first_run = True

    def _set_archives_view(self, type):
        """
        Switch to either EX or SP view in page_archives

        Args:
            type(str): ex or sp
        """
        for n in range(3):
            self.device.screenshot()
            if type in 'ex':
                self.appear_then_click(WAR_ARCHIVES_EX_OFF)
                continue
            elif type in 'sp':
                self.appear_then_click(WAR_ARCHIVES_SP_OFF)
                continue
            else:
                raise CampaignNameError

    def _get_archives_entrance(self, name):
        """
        Create entrance button to target archive campaign
        using a template acquired by event folder name

        TODO: Each server have different selectable campaign
              Need something similar to commission to scroll
              or turn page. CN/JP have more than 4 atm.

        Args:
            name(str): event folder name
        """
        template = dic_archives_template[name]

        sim, point = template.match_result(self.device.image)
        if sim < 0.85:
            raise CampaignNameError

        button = area_offset(area=(-12, -12, 44, 32), offset=point)
        color = get_color(self.device.image, button)
        entrance = Button(area=button, color=color, button=button, name=name)
        return entrance

    def _in_archives_campaign(self):
        """
        Check if already in archives campaign
        """
        for n in range(3):
            self.device.screenshot()
            if self.appear(WAR_ARCHIVES_CAMPAIGN_CHECK, offset=(20, 20)):
                return True
        return False


    def ui_goto_archives_campaign(self, type):
        """
        Transition to page_archives then to the configured
        event campaign map

        Args:
            type (str): 'ex' or 'sp'.
        """
        # First run, regardless of current location
        # Start from page_main
        if self.first_run:
            self.first_run = False
            self.ui_ensure(destination=page_main)

        # If not in archives campaign map
        # then transition to configured location
        if not self._in_archives_campaign():
            self.ui_ensure(destination=page_archives)

            # Click approriate switch 'ex' or 'sp'
            # Wait same amount of time as stage_icon_spawn
            self._set_archives_view(type)
            self.handle_stage_icon_spawn()

            # Acquire approriate event entrance based on template
            # Wait for stage_icon_spawn
            archives_entrance = self._get_archives_entrance(self.config.WAR_ARCHIVES_NAME)
            self.ui_click(archives_entrance, appear_button=WAR_ARCHIVES_CHECK, check_button=WAR_ARCHIVES_CAMPAIGN_CHECK,
                          skip_first_screenshot=True)
            self.handle_stage_icon_spawn()

    def campaign_set_chapter(self, name, mode='normal'):
        """
        Overridden especially for war_archives usage

        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
        """
        chapter, _ = self._campaign_separate_name(name)

        if chapter in 'abcd':
            self.ui_goto_archives_campaign('ex')
            if chapter in 'ab':
                self.campaign_ensure_mode('normal')
            elif chapter in 'cd':
                self.campaign_ensure_mode('hard')
            self.campaign_ensure_chapter(index=chapter)
        elif chapter == 'sp':
            self.ui_goto_archives_campaign('sp')
            self.campaign_ensure_chapter(index=chapter)
        else:
            logger.warning(f'Unknown campaign chapter: {name}')