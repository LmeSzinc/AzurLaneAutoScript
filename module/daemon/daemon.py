from module.combat.combat import Combat
from module.daemon.assets import *
from module.handler.ambush import MAP_AMBUSH_EVADE
from module.handler.mystery import MysteryHandler
from module.handler.popup import PopupHandler
from module.handler.urgent_commission import UrgentCommissionHandler
from module.map.map_fleet_preparation import FleetPreparation


class AzurLaneDaemon(FleetPreparation, Combat, UrgentCommissionHandler, MysteryHandler,
                     PopupHandler):
    def daemon(self):

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
            if self.handle_battle_status(save_get_items=False):
                self.combat_status(save_get_items=False, expected_end='no_searching')
                continue

            # Map operation
            if self.appear_then_click(MAP_AMBUSH_EVADE):
                self.device.sleep(1)
                continue
            if self.appear_then_click(STRATEGY_OPEN):
                continue

            # Map preparation
            if self.config.ENABLE_SEMI_MAP_PREPARATION:
                if self.appear_then_click(MAP_PREPARATION, interval=2):
                    continue
                if self.appear_then_click(FLEET_PREPARATION, interval=2):
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
                if self.appear_then_click(STORY_SKIP, offset=True, interval=2):
                    continue
                if self.handle_popup_confirm():
                    continue
                if self.appear_then_click(STORY_CHOOCE, offset=True, interval=2):
                    continue
                if self.appear_then_click(STORY_CHOOCE_2, offset=True, interval=2):
                    continue

            # End
            # No end condition, stop it manually.

        return True
