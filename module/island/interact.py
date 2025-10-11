from module.logger import logger
from module.island.assets import *
from module.ui.ui import UI


class IslandInteract(UI):
    # just a random spot to dismiss dialogs
    BTN_EMPTY = Button(area=(500, 20, 510, 30), color=(), button=(500, 20, 510, 30), name='Island Popup Dismiss')

    def goto_ui(self, target_page):
        return self.ui_goto(target_page, get_ship=False)

    def dismiss(self, repeats=1):
        """
        Dismiss any popups if exist
        """
        for _ in range(repeats):
            self.device.click(self.BTN_EMPTY)
            self.device.sleep(0.1)
