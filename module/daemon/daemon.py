from module.campaign.campaign_base import CampaignBase
from module.daemon.daemon_base import DaemonBase
from module.exception import CampaignEnd
from module.handler.ambush import MAP_AMBUSH_EVADE
from module.map.map_operation import FLEET_PREPARATION, MAP_PREPARATION


class AzurLaneDaemon(DaemonBase, CampaignBase):
    def run(self):
        while 1:
            self.device.screenshot()

            # If is running a combat, do nothing.
            if self.is_combat_executing():
                continue

            # Combat
            if self.combat_appear():
                self.combat_preparation()
            try:
                if self.handle_battle_status():
                    self.combat_status(expected_end='no_searching')
                    continue
            except CampaignEnd:
                continue

            # Map operation
            if self.appear_then_click(MAP_AMBUSH_EVADE, offset=(20, 20)):
                self.device.sleep(1)
                continue
            if self.handle_mystery_items():
                continue

            # Map preparation
            if self.config.Daemon_EnterMap:
                if self.appear_then_click(MAP_PREPARATION, offset=(20, 20), interval=2):
                    continue
                if self.appear_then_click(FLEET_PREPARATION, offset=(20, 50), interval=2):
                    continue

            # Retire
            if self.handle_retirement():
                continue

            # Emotion
            pass

            # Urgent commission
            if self.handle_urgent_commission():
                continue

            # Popups
            if self.handle_guild_popup_cancel():
                return True
            if self.handle_vote_popup():
                continue

            # Story
            if self.story_skip():
                continue

            # End
            # No end condition, stop it manually.

        return True


if __name__ == '__main__':
    b = AzurLaneDaemon('alas', task='Daemon')
    b.run()
