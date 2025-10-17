from module.base.timer import Timer
from module.shop.assets import *
from module.shop.shop_core import CoreShop_250814
from module.shop.shop_general import GeneralShop_250814
from module.shop.shop_guild import GuildShop_250814
from module.shop.shop_medal import MedalShop2_250814
from module.shop.shop_merit import MeritShop_250814
from module.shop.ui import ShopUI
from module.shop_event.clerk import ItemNotFoundError
from module.shop_event.shop_event import EventShop
from module.ui.assets import SHOP_GOTO_MUNITIONS
from module.ui.page import page_shop, page_munitions


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

        # Event Shop
        if self.config.EventShop_Enable:
            self.ui_goto_main()
            self.ui_ensure(page_shop)
            timeout = Timer(2, count=4)
            for _ in self.loop():
                if self.appear(page_munitions.check_button, threshold=20):
                    break
                if timeout.reached():
                    self.device.click(SHOP_GOTO_MUNITIONS)
                    timeout.reset()

            if self.shop_nav_250814.get(main=self) == NAV_EVENT:
                self.device.click_record_clear()
                for _ in range(7):  # Try event shop up to 7 times, should be enough
                    try:
                        EventShop(self.config, self.device).run()
                        break
                    except ItemNotFoundError:
                        # Refresh the event shop to avoid random item not found error
                        self.shop_nav_250814.set(NAV_GENERAL, main=self)
                        self.device.click_record_clear()
                        self.shop_nav_250814.set(NAV_EVENT, main=self)

        # Munitions shops
        self.ui_goto_shop()
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