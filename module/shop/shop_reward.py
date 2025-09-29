from module.shop.shop_core import CoreShop_250814
from module.shop.shop_general import GeneralShop_250814
from module.shop.shop_guild import GuildShop_250814
from module.shop.shop_medal import MedalShop2_250814
from module.shop.shop_merit import MeritShop_250814
from module.shop.ui import ShopUI
from module.shop_event.clerk import ItemNotFoundError
from module.shop_event.shop_event import EventShop


class RewardShop(ShopUI):
    def run_frequent(self):
        # Munitions shops
        if self.config.SERVER in ['tw']:
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        self.ui_goto_shop()
        self.device.click_record_clear()
        self.shop_tab_250814.set(main=self, upper=1)
        self.shop_nav_250814.set(main=self, left=1)
        GeneralShop_250814(self.config, self.device).run()

        self.config.task_delay(server_update=True)

    def run_once(self):
        # Munitions shops
        if self.config.SERVER in ['tw']:
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        self.ui_goto_shop()
        if self.config.EventShop_Enable:
            self.device.click_record_clear()
            self.shop_tab_250814.set(main=self, bottom=1)
            if self.shop_tab_250814.get_active(main=self) == 2:
                for _ in range(7):  # Try event shop up to 7 times, should be enough
                    try:
                        EventShop(self.config, self.device).run()
                        break
                    except ItemNotFoundError:
                        # Refresh the event shop to avoid random item not found error
                        self.shop_tab_250814.set(main=self, upper=1)
                        self.device.click_record_clear()
                        self.shop_tab_250814.set(main=self, upper=3)

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
