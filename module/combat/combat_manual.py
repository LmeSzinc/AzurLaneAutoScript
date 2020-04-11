from module.base.base import ModuleBase
from module.combat.assets import MOVE_DOWN


class CombatManual(ModuleBase):
    auto_mode_checked = False
    manual_executed = False

    def combat_manual_reset(self):
        self.manual_executed = False

    def handle_combat_stand_still_in_the_middle(self):
        if self.config.COMBAT_AUTO_MODE != 'stand_still_in_the_middle':
            return False

        self.device.long_click(MOVE_DOWN, duration=0.8)
        return True

    def handle_combat_manual(self):
        if self.manual_executed or not self.auto_mode_checked:
            return False

        if self.handle_combat_stand_still_in_the_middle():
            self.manual_executed = True
            return True

        return False
