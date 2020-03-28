from module.handler.assets import STRATEGY_OPEN_1
from module.handler.info_bar import InfoBarHandler


class StrategyHandler(InfoBarHandler):
    def handle_opened_strategy_bar(self):
        if self.appear_then_click(STRATEGY_OPEN_1):
            self.device.sleep(0.5)
            return True

        return False
