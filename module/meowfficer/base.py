from module.meowfficer.assets import *
from module.ui.assets import MEOWFFICER_CHECK, MEOWFFICER_INFO
from module.ui.ui import UI


class MeowfficerBase(UI):
    def meow_additional(self):
        """
        Handle additional clauses
        that may occur in between screens

        Returns:
            bool:
        """
        if self.appear_then_click(MEOWFFICER_INFO, offset=(30, 30), interval=3):
            return True

        return False

    def handle_meow_popup_confirm(self):
        """
        Confirm the popup; can mean close
        the popup and allow the action

        Returns:
            bool:
        """
        if self.appear_then_click(MEOWFFICER_CONFIRM, offset=(40, 20), interval=5):
            return True
        else:
            return False

    def handle_meow_popup_cancel(self):
        """
        Cancel the popup; can mean close
        the popup or to not allow the action

        Returns:
            bool:
        """
        if self.appear_then_click(MEOWFFICER_CANCEL, offset=(40, 20), interval=5):
            return True
        else:
            return False

    def handle_meow_popup_dismiss(self):
        """
        Dismiss the popup; neither confirm
        or cancel the action

        Returns:
            bool:
        """
        if self.appear(MEOWFFICER_CONFIRM, offset=(40, 20), interval=5):
            self.device.click(MEOWFFICER_CHECK)
            return True
        elif self.appear(MEOWFFICER_CANCEL, offset=(40, 20), interval=5):
            self.device.click(MEOWFFICER_CHECK)
            return True
        else:
            return False
