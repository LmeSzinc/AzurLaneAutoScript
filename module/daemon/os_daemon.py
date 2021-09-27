from module.exception import *
from module.logger import logger
from module.os_combat.combat import Combat, ContinuousCombat
from module.os_handler.port import PortHandler, PORT_ENTER


class AzurLaneDaemon(Combat, PortHandler):
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

            # Port repair
            if self.appear(PORT_ENTER, offset=(20, 20), interval=30):
                self.port_enter()
                self.port_dock_repair()
                self.port_quit()
                self.interval_reset(PORT_ENTER)
                logger.info('Port repair finished, move your fleet out of the port in 30s to avoid repairing again')

            # End
            # No end condition, stop it manually.

        return True
