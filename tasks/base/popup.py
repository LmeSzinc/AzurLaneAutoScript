from module.base.base import ModuleBase
from tasks.base.assets.assets_base_popup import *


class PopupHandler(ModuleBase):
    def handle_reward(self, interval=5) -> bool:
        """
        Args:
            interval:

        Returns:
            If handled.
        """
        if self.appear_then_click(GET_REWARD, interval=interval):
            return True

        return False

    def handle_battle_pass_notification(self, interval=5) -> bool:
        """
        Popup notification that you enter battle pass the first time.

        Args:
            interval:

        Returns:
            If handled.
        """
        if self.appear_then_click(BATTLE_PASS_NOTIFICATION, interval=interval):
            return True

        return False
