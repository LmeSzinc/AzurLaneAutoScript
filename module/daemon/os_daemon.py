from module.campaign.campaign_base import CampaignBase
from module.daemon.assets import *
from module.exception import *
from module.os_combat.assets import *
from module.os_combat.combat import Combat, ContinuousCombat
from module.os_handler.map_event import MapEventHandler


class AzurLaneDaemon(Combat):
    def daemon(self):
        self.device.disable_stuck_detection()

        while 1:
            self.device.screenshot()

            # If is running a combat, do nothing.
            if self.is_combat_executing():
                continue

            # Combat
            if self.combat_appear():
                self.combat_preparation()
            try:
                if self.handle_battle_status(save_get_items=False):
                    self.combat_status(save_get_items=False, expected_end='no_searching')
                    continue
            except (CampaignEnd, ContinuousCombat):
                continue

            # Map operation

            # Map preparation

            # Retire
            pass

            # Emotion
            pass

            # Urgent commission
            if self.handle_urgent_commission(save_get_items=False):
                continue

            # Story
            if self.config.ENABLE_OS_SEMI_STORY_SKIP:
                self.story_skip()

            self.handle_map_event()

            # End
            # No end condition, stop it manually.

        return True