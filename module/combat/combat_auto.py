from module.base.base import ModuleBase
from module.base.timer import Timer
from module.combat.assets import COMBAT_AUTO, COMBAT_AUTO_2X, COMBAT_AUTO_SWITCH
from module.logger import logger


class CombatAuto(ModuleBase):
    auto_skip_timer = Timer(1)
    auto_click_interval_timer = Timer(1)
    auto_mode_checked = False
    auto_mode_click_timer = Timer(5)

    def combat_auto_reset(self):
        self.auto_mode_click_timer.reset()
        self.auto_skip_timer.reset()
        self.auto_mode_checked = False

    def handle_combat_auto(self, auto):
        """
        Args:
            auto (str): Combat auto mode.

        Returns:
            bool: If executed
        """
        if self.auto_mode_checked:
            return False
        if self.auto_mode_click_timer.reached():
            logger.info('Combat auto check timer reached')
            self.auto_mode_checked = True
            return False
        if not self.auto_skip_timer.reached():
            return False
        if not self.auto_click_interval_timer.reached():
            return False

        auto = auto == 'combat_auto'
        if self.appear(COMBAT_AUTO, offset=(20, 20)) or self.appear(COMBAT_AUTO_2X, offset=(20, 20)):
            if auto:
                self.device.click(COMBAT_AUTO_SWITCH)
                self.auto_click_interval_timer.reset()
                return True
        else:
            if not auto:
                self.device.click(COMBAT_AUTO_SWITCH)
                self.auto_click_interval_timer.reset()
                return True

        return False
