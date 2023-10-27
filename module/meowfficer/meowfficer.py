from module.meowfficer.buy import MeowfficerBuy
from module.meowfficer.fort import MeowfficerFort
from module.meowfficer.train import MeowfficerTrain
from module.ui.page import page_meowfficer


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
                and not self.config.Meowfficer_FortChoreMeowfficer \
                and not self.config.MeowfficerTrain_Enable:
            self.config.Scheduler_Enable = False
            self.config.task_stop()

        self.ui_ensure(page_meowfficer)

        if self.config.Meowfficer_BuyAmount > 0:
            self.meow_buy()
        if self.config.Meowfficer_FortChoreMeowfficer:
            self.meow_fort()

        # Train
        if self.config.MeowfficerTrain_Enable:
            self.meow_train()
            if self.config.MeowfficerTrain_Mode == 'seamlessly':
                self.meow_enhance()
            elif self.meow_is_sunday():
                self.meow_enhance()
            else:
                pass

        # Scheduler
        if self.config.MeowfficerTrain_Enable:
            # Meowfficer training duration:
            # - Blue, 2.0h ~ 2.5h
            # - Purple, 5.5h ~ 6.5h
            # - Gold, 9.5h ~ 10.5h
            # Delay 2.5h ~ 3.5h when having meowfficers under training
            self.config.task_delay(minute=(150, 210), server_update=True)
        else:
            self.config.task_delay(server_update=True)
