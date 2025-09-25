from module.shop.assets import *
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
        if self.config.SERVER in ['tw']:
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        self.ui_goto_shop()
        self.device.click_record_clear()
        self.shop_nav_250814.set(NAV_GENERAL, main=self)
        self.shop_tab_250814.set(TAB_GENERAL, main=self)
        GeneralShop_250814(self.config, self.device).run()

        self.config.task_delay(server_update=True)

    def run_once(self):
        if self.config.SERVER in ['tw']:
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        # Munitions shops
        self.ui_goto_shop()
        if self.config.EventShop_Enable:
            self.device.click_record_clear()
            self.shop_tab_250814.set(main=self, bottom=1)
            if self.shop_tab_250814.get_active(main=self) == 2:
                while 1:
                    try:
                        EventShop(self.config, self.device).run()
                        break
                    except ItemNotFoundError:
                        # Refresh the event shop to avoid random item not found error
                        self.shop_tab_250814.set(main=self, upper=1)
                        self.device.click_record_clear()
                        self.shop_tab_250814.set(main=self, upper=3)

        self.device.click_record_clear()
        self.shop_nav_250814.set(NAV_GENERAL, main=self)
        self.shop_tab_250814.set(TAB_MERIT, main=self)
        MeritShop_250814(self.config, self.device).run()

        self.device.click_record_clear()
        self.shop_nav_250814.set(NAV_GENERAL, main=self)
        self.shop_tab_250814.set(TAB_GUILD, main=self)
        GuildShop_250814(self.config, self.device).run()

        # core limited, core monthly, medal, prototype
        self.device.click_record_clear()
        self.shop_nav_250814.set(NAV_MONTHLY, main=self)
        self.shop_tab_250814.set(TAB_CORE_MONTHLY, main=self)
        CoreShop_250814(self.config, self.device).run()

        self.device.click_record_clear()
        self.shop_nav_250814.set(NAV_MONTHLY, main=self)
        self.shop_tab_250814.set(TAB_MEDAL, main=self)
        MedalShop2_250814(self.config, self.device).run()

        self.config.task_delay(server_update=True)


if __name__ == '__main__':
    self = RewardShop('alas')
    self.device.screenshot()
    self.run_once()