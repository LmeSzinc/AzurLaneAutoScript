from module.base.timer import Timer
from module.campaign.campaign_base import CampaignBase
from module.coalition.assets import *
from module.coalition.ui import CoalitionUI
from module.exception import CampaignEnd
from module.logger import logger
from module.os_ash.assets import BATTLE_STATUS


class CoalitionCombat(CoalitionUI, CampaignBase):
    battle_status_click_interval = 2

    def coalition_combat_re_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: battle_status
            out: is_combat_executing
        """
        logger.info('Coalition combat re-enter')
        status_clicked = False
        click_timer = Timer(0.3)
        click_last = Timer(2)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_combat_loading():
                break
            if self.in_coalition():
                raise CampaignEnd

            if self.appear_then_click(BATTLE_STATUS, offset=(80, 20), interval=2):
                # About (+53, +3)
                continue
            if self.appear_then_click(COALITION_REWARD_CONFIRM, offset=(20, 20), interval=2):
                # Stop clicking BATTLE_STATUS because combat ends
                status_clicked = False
                continue
            if self.handle_battle_status():
                status_clicked = True
                click_last.reset()
                continue
            # Keep clicking BATTLE_STATUS to skip animations
            if status_clicked:
                if click_timer.reached() and not click_last.reached():
                    self.device.click(BATTLE_STATUS)
                    click_timer.reset()

    def coalition_combat(self):
        """
        Pages:
            in: is_coalition
            out: is_coalition
        """
        self.battle_count = 0
        self.combat_preparation(emotion_reduce=False)

        try:
            while 1:
                logger.hr(f'{self.FUNCTION_NAME_BASE}{self.battle_count}', level=2)
                self.auto_search_combat_execute(
                    emotion_reduce=self.battle_count == 0 or self.config.Coalition_Fleet == 'single',
                    fleet_index=1
                )
                self.coalition_combat_re_enter()
                self.battle_count += 1
        except CampaignEnd:
            logger.info('Coalition combat end.')
