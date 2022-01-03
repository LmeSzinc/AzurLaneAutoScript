from module.base.base import ModuleBase
from module.logger import logger
from module.shop.shop_core import CoreShop
from module.shop.shop_general import GeneralShop
from module.shop.shop_guild import GuildShop
from module.shop.shop_medal import MedalShop
from module.shop.shop_merit import MeritShop


class RewardShop(ModuleBase):
    def run_frequent(self):
        GeneralShop(self.config, self.device).run()

        self.config.task_delay(server_update=True)

    def run_once(self):
        MeritShop(self.config, self.device).run()

        CoreShop(self.config, self.device).run()

        GuildShop(self.config, self.device).run()

        MedalShop(self.config, self.device).run()

        self.config.task_delay(server_update=True)
