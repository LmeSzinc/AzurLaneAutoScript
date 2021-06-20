from module.campaign.campaign_base import CampaignBase
from module.daemon.assets import *
from module.exception import *
from module.handler.ambush import MAP_AMBUSH_EVADE


class AzurLaneDaemon(CampaignBase):
    def daemon(self):
        self.device.disable_stuck_detection()

        while 1:
            self.device.screenshot()

            # If is running a combat, do nothing.
            if self.is_combat_executing():
                continue

            # Combat
            if self.combat_appear():
                # if self.handle_combat_automation_set(auto=True):
                #     continue
                # self.device.click(BATTLE_PREPARATION)
                self.combat_preparation()
            try:
                if self.handle_battle_status(save_get_items=False):
                    self.combat_status(save_get_items=False, expected_end='no_searching')
                    continue
            except CampaignEnd:
                continue

            # Map operation
            if self.appear_then_click(MAP_AMBUSH_EVADE):
                self.device.sleep(1)
                continue
            if self.appear_then_click(STRATEGY_OPEN):
                continue

            # Map preparation
            if self.config.ENABLE_SEMI_MAP_PREPARATION:
                if self.appear_then_click(MAP_PREPARATION, offset=(20, 20), interval=2):
                    continue
                if self.appear_then_click(FLEET_PREPARATION, offset=(20, 20), interval=2):
                    continue

            # Retire
            pass

            # Emotion
            pass

            # Urgent commission
            if self.handle_urgent_commission(save_get_items=False):
                continue

            # Story
            if self.config.ENABLE_SEMI_STORY_SKIP:
                self.story_skip()

            # End
            # No end condition, stop it manually.

        return True
