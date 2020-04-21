from module.base.base import ModuleBase
from module.base.timer import Timer
from module.handler.assets import *


class InfoBarHandler(ModuleBase):
    def info_bar_count(self):
        if self.appear(INFO_BAR_3):
            return 3
        elif self.appear(INFO_BAR_2):
            return 2
        elif self.appear(INFO_BAR_1):
            return 1
        else:
            return 0

    def handle_info_bar(self):
        if self.info_bar_count():
            self.wait_until_disappear(INFO_BAR_1)
            return True
        else:
            return False
        # self.sleep(1)

    def ensure_no_info_bar(self, timeout=0.6):
        timeout = Timer(timeout)
        timeout.start()
        while 1:
            self.device.screenshot()
            self.handle_info_bar()

            if timeout.reached():
                break
