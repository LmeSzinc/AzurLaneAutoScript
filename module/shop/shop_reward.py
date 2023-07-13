from module.base.decorator import Config
from module.logger import logger
from module.shop.shop_core import CoreShop
from module.shop.shop_general import GeneralShop
from module.shop.shop_guild import GuildShop
from module.shop.shop_medal import MedalShop2
from module.shop.shop_merit import MeritShop
from module.shop.ui import ShopUI


class RewardShop(ShopUI):
    def run_frequent(self):
        if self.config.SERVER in ['cn', 'en', 'jp']:
            logger.warning(f'Task ShopOnce is disabled in server {self.config.SERVER.upper()} until assets are updated')
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        # Munitions shops
        self.ui_goto_shop()

        GeneralShop(self.config, self.device).run()

        self.config.task_delay(server_update=True)

    @Config.when(SERVER='tw')
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

        # 2022.06.01 Medal shop has been moved to page_munitions
        # Now the left most shop, its UI has changed considerably
        if self.shop_bottom_navbar_ensure(left=1):
            MedalShop2(self.config, self.device).run()

        # Cannot go back to general shop so don't stay in page_munitions
        self.ui_goto_main()
        self.config.task_delay(server_update=True)

    @Config.when(SERVER=None)
    def run_once(self):
        if self.config.SERVER in ['cn', 'en', 'jp']:
            logger.warning(f'Task ShopOnce is disabled in server {self.config.SERVER.upper()} until assets are updated')
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        # Munitions shops
        self.ui_goto_shop()

        current = self._shop_bottom_navbar.get_active(main=self)
        logger.info(f'Shop nav actives at left={current}')

        if current is not None:
            current += 1
            # core_monthly, core, merit, general, event
            # core, merit, general, event, event (2 event shops sometimes)
            if self.shop_bottom_navbar_ensure(left=current - 1):
                MeritShop(self.config, self.device).run()
            if current - 3 >= 1:
                if self.shop_bottom_navbar_ensure(left=current - 3):
                    CoreShop(self.config, self.device).run()
            else:
                logger.warning('Cannot navigate to core shop, skip')
        else:
            logger.error('Cannot get the position of general shop, skip merit shop and core shop')

        self.shop_swipe()
        # gift, meta, medal, guild, prototype
        # meta, gift, medal, guild, prototype [EN]
        if self.shop_bottom_navbar_ensure(left=4):
            GuildShop(self.config, self.device).run()

        if self.shop_bottom_navbar_ensure(left=3):
            MedalShop2(self.config, self.device).run()

        # Cannot go back to general shop so don't stay in page_munitions
        self.ui_goto_main()
        self.config.task_delay(server_update=True)
