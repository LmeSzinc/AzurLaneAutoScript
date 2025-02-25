from module.shop.shop_core import CoreShop
from module.shop.shop_general import GeneralShop
from module.shop.shop_guild import GuildShop
from module.shop.shop_medal import MedalShop2
from module.shop.shop_merit import MeritShop
from module.shop.ui import ShopUI
from module.shop_event.shop_event import EventShop
from module.shop_event.ui import OCR_EVENT_SHOP_SECOND_ENSURE


class RewardShop(ShopUI):
    def run_frequent(self):
        # Munitions shops
        self.ui_goto_shop()

        self.shop_tab.set(main=self, left=2)
        self.shop_nav.set(main=self, upper=1)
        GeneralShop(self.config, self.device).run()

        self.config.task_delay(server_update=True)

    def run_once(self):
        # Munitions shops
        if self.config.EventShop_Enable:
            self.ui_goto_event_shop()
            if self.shop_tab.get_active(main=self) == 2:
                EventShop(self.config, self.device).run()
                text = OCR_EVENT_SHOP_SECOND_ENSURE.ocr(self.device.image)
                if text != "":
                    self.shop_nav.set(main=self, upper=2)
                    EventShop(self.config, self.device).run()
        else:
            self.ui_goto_shop()

        self.shop_tab.set(main=self, left=2)
        self.shop_nav.set(main=self, upper=2)
        MeritShop(self.config, self.device).run()

        self.shop_tab.set(main=self, left=2)
        self.shop_nav.set(main=self, upper=3)
        GuildShop(self.config, self.device).run()

        # core limited, core monthly, medal, prototype
        self.shop_tab.set(main=self, left=1)
        self.shop_nav.set(main=self, upper=2)
        CoreShop(self.config, self.device).run()

        self.shop_tab.set(main=self, left=1)
        self.shop_nav.set(main=self, upper=3)
        MedalShop2(self.config, self.device).run()

        self.config.task_delay(server_update=True)
