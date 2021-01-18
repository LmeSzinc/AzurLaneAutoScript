from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2
from module.combat.combat import Combat
from module.guild.assets import BATTLE_STATUS_CF, EXP_INFO_CF


class GuildCombat(Combat):
    def handle_battle_status(self, save_get_items=False):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if self.appear_then_click(BATTLE_STATUS_CF, screenshot=save_get_items, genre='status',
                                  interval=self.battle_status_click_interval):
            if not save_get_items:
                self.device.sleep((0.25, 0.5))
            return True

        return False

    def handle_get_items(self, save_get_items=False):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if self.appear_then_click(GET_ITEMS_1, screenshot=save_get_items, genre='get_items', offset=5,
                                  interval=self.battle_status_click_interval):
            self.interval_reset(BATTLE_STATUS_CF)
            return True
        if self.appear_then_click(GET_ITEMS_2, screenshot=save_get_items, genre='get_items', offset=5,
                                  interval=self.battle_status_click_interval):
            self.interval_reset(BATTLE_STATUS_CF)
            return True

        return False

    def handle_exp_info(self):
        """
        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if self.appear_then_click(EXP_INFO_CF):
            self.device.sleep((0.25, 0.5))
            return True

        return False
