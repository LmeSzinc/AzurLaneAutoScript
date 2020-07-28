from module.base.base import ModuleBase
from module.combat.assets import *


class CombatManual(ModuleBase):
    auto_mode_checked = False
    manual_executed = False

    def combat_manual_reset(self):
        self.manual_executed = False

    def handle_combat_stand_still_in_the_middle(self, auto):
        """
        Args:
            auto (str): Combat auto mode.

        Returns:
            bool: If executed
        """
        if auto != 'stand_still_in_the_middle':
            return False

        self.device.long_click(MOVE_DOWN, duration=0.8)
        return True

    def handle_combat_weapon_release(self):
        if self.appear_then_click(READY_AIR_RAID, interval=5):
            return True
        if self.appear_then_click(READY_TORPEDO, interval=5):
            return True

        return False

    def handle_combat_manual(self, auto):
        """
        Args:
            auto (str): Combat auto mode.

        Returns:
            bool: If executed
        """
        if self.manual_executed or not self.auto_mode_checked:
            return False

        if self.handle_combat_stand_still_in_the_middle(auto):
            self.manual_executed = True
            return True

        return False
