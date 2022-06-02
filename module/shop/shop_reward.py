from module.gacha.ui import GachaUI
from module.shop.shop_core import CoreShop
from module.shop.shop_general import GeneralShop
from module.shop.shop_guild import GuildShop
from module.shop.shop_merit import MeritShop
from module.shop.ui import ShopUI


class RewardShop(ShopUI, GachaUI):
    def run_frequent(self):
        # Munitions shops
        self.ui_goto_shop()

        GeneralShop(self.config, self.device).run()

        self.config.task_delay(server_update=True)

    def run_once(self):
        # Munitions shops
        self.ui_goto_shop()
        self.shop_swipe()

        if self.shop_bottom_navbar_ensure(left=5):
            MeritShop(self.config, self.device).run()

        if self.shop_bottom_navbar_ensure(left=4):
            CoreShop(self.config, self.device).run()

        if self.shop_bottom_navbar_ensure(left=2):
            GuildShop(self.config, self.device).run()

        # 2022.06.01 Medal shop and gacha shop have been moved to shop
        # Gacha shops
        # self.ui_goto_gacha()
        # if not self.gacha_side_navbar_ensure(bottom=2):
        #     return
        # shop = MedalShop(self.config, self.device)
        # for _ in [1, 2]:
        #     if self.gacha_bottom_navbar_ensure(left=_, is_build=False):
        #         shop.run()

        self.config.task_delay(server_update=True)
