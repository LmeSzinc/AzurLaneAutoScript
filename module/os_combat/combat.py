from module.combat.assets import *
from module.combat.combat import Combat as Combat_
from module.logger import logger
from module.os_combat.assets import *
from module.os_handler.assets import *
from module.os_handler.map_event import MapEventHandler


class Combat(Combat_, MapEventHandler):
    def combat_appear(self):
        """
        Returns:
            bool: If enter combat.
        """
        if not self.is_in_map():
            if self.is_combat_loading():
                return True

        if self.appear(BATTLE_PREPARATION):
            return True
        if self.appear(SIREN_PREPARATION):
            return True
        if self.appear(BATTLE_PREPARATION_WITH_OVERLAY) and self.handle_combat_automation_confirm():
            return True

        return False

    def combat_preparation(self, balance_hp=False, emotion_reduce=False, auto='combat_auto', fleet_index=1):
        """
        Args:
            balance_hp (bool):
            emotion_reduce (bool):
            auto (str):
            fleet_index (int):
        """
        logger.info('Combat preparation.')
        skip_first_screenshot = True

        # if emotion_reduce:
        #     self.emotion.wait(fleet=fleet_index)
        if balance_hp:
            self.hp_balance()

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(BATTLE_PREPARATION):
                if self.handle_combat_automation_set(auto=auto == 'combat_auto'):
                    continue
            # if self.handle_retirement():
            #     continue
            # if self.handle_combat_low_emotion():
            #     continue
            # if balance_hp and self.handle_emergency_repair_use():
            #     continue
            if self.appear_then_click(BATTLE_PREPARATION, interval=2):
                continue
            if self.appear_then_click(SIREN_PREPARATION, interval=2):
                continue
            if self.handle_popup_confirm('ENHANCED_ENEMY'):
                continue
            if self.handle_combat_automation_confirm():
                continue
            if self.handle_story_skip():
                continue

            # End
            if self.is_combat_executing():
                # if emotion_reduce:
                #     self.emotion.reduce(fleet_index)
                break

    def handle_get_items(self, save_get_items=False):
        if self.appear(GET_ITEMS_1, offset=5, interval=self.battle_status_click_interval):
            self.device.click(CLICK_SAFE_AREA)
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            return True
        if self.appear(GET_ITEMS_2, offset=5, interval=self.battle_status_click_interval):
            self.device.click(CLICK_SAFE_AREA)
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            return True
        if self.appear(GET_ADAPTABILITY, offset=5, interval=self.battle_status_click_interval):
            self.device.click(CLICK_SAFE_AREA)
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            return True

        return False

    def _os_combat_expected_end(self):
        if self.handle_map_event():
            return False

        return self.is_in_map()

    def combat_status(self, save_get_items=False, expected_end=None):
        super().combat_status(save_get_items=False, expected_end=self._os_combat_expected_end)
        self.ensure_no_map_event()
