from module.logger import logger
from module.meowfficer.assets import *
from module.meowfficer.buy import MeowfficerBuy
from module.meowfficer.fort import MeowfficerFort
from module.meowfficer.train import MeowfficerTrain
from module.ui.ui import page_meowfficer


class RewardMeowfficer(MeowfficerBuy, MeowfficerFort, MeowfficerTrain):
    def run(self):
        """
        Execute buy, enhance, train, and fort operations
        if enabled in configurations

        Pages:
            in: Any page
            out: page_meowfficer
        """
        if self.config.Meowfficer_BuyAmount <= 0 \
                and not self.config.Meowfficer_TrainMeowfficer \
                and not self.config.Meowfficer_FortChoreMeowfficer:
            self.config.Scheduler_Enable = False
            self.config.task_stop()

        self.ui_ensure(page_meowfficer)

        if self.config.Meowfficer_BuyAmount > 0:
            self.meow_buy()
        if self.config.Meowfficer_EnhanceIndex > 0:
            self.meow_enhance()
        if self.config.Meowfficer_TrainMeowfficer:
            self.meow_train()
        if self.config.Meowfficer_FortChoreMeowfficer:
            self.meow_fort()

        self.config.task_delay(server_update=True)
