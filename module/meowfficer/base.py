from module.meowfficer.assets import *
from module.ui.assets import MEOWFFICER_INFO
from module.ui.ui import UI


class MeowfficerBase(UI):
    def meow_additional(self):
        if self.appear_then_click(MEOWFFICER_INFO, offset=(30, 30), interval=3):
            return True

        return False

    def handle_meow_popup_confirm(self):
        if self.appear_then_click(MEOWFFICER_CONFIRM, offset=(40, 20), interval=5):
            return True
        else:
            return False
