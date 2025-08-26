from module.shop.shop_core import CoreShop, CoreShop_250814
from module.shop.shop_general import GeneralShop, GeneralShop_250814
from module.shop.shop_guild import GuildShop, GuildShop_250814
from module.shop.shop_medal import MedalShop2, MedalShop2_250814
from module.shop.shop_merit import MeritShop, MeritShop_250814
from module.shop.ui import ShopUI


class RewardShop(ShopUI):
    def run_frequent(self):
        # Munitions shops
        self.ui_goto_shop()
        if self.config.SERVER in ['tw']:
            self.device.click_record_clear()
            self.shop_tab.set(main=self, left=2)
            self.shop_nav.set(main=self, upper=1)
            GeneralShop(self.config, self.device).run()
        elif self.config.SERVER in ['cn']:
            self.device.click_record_clear()
            self.shop_tab_250814.set(main=self, upper=1)
            self.shop_nav_250814.set(main=self, left=1)
            GeneralShop_250814(self.config, self.device).run()
        self.config.task_delay(server_update=True)

    def run_once(self):
        # Munitions shops
        self.ui_goto_shop()
        if self.config.SERVER in ['tw']:
            self.device.click_record_clear()
            self.shop_tab.set(main=self, left=2)
            self.shop_nav.set(main=self, upper=2)
            MeritShop(self.config, self.device).run()

            self.device.click_record_clear()
            self.shop_tab.set(main=self, left=2)
            self.shop_nav.set(main=self, upper=3)
            GuildShop(self.config, self.device).run()

            # core limited, core monthly, medal, prototype
            self.device.click_record_clear()
            self.shop_tab.set(main=self, left=1)
            self.shop_nav.set(main=self, upper=2)
            CoreShop(self.config, self.device).run()

            self.device.click_record_clear()
            self.shop_tab.set(main=self, left=1)
            self.shop_nav.set(main=self, upper=3)
            MedalShop2(self.config, self.device).run()
        elif self.config.SERVER in ['cn']:
            self.device.click_record_clear()
            self.shop_tab_250814.set(main=self, upper=1)
            self.shop_nav_250814.set(main=self, left=2)
            MeritShop_250814(self.config, self.device).run()

            self.device.click_record_clear()
            self.shop_tab_250814.set(main=self, upper=1)
            self.shop_nav_250814.set(main=self, left=3)
            GuildShop_250814(self.config, self.device).run()

            # core limited, core monthly, medal, prototype
            self.device.click_record_clear()
            self.shop_tab_250814.set(main=self, upper=2)
            self.monthly_shop_nav_250814.set(main=self, left=2)
            CoreShop_250814(self.config, self.device).run()

            self.device.click_record_clear()
            self.shop_tab_250814.set(main=self, upper=2)
            self.monthly_shop_nav_250814.set(main=self, left=3)
            MedalShop2_250814(self.config, self.device).run()

        self.config.task_delay(server_update=True)
