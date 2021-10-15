from datetime import datetime, timedelta, timezone
from module.gacha.ui import GachaUI
from module.logger import logger
from module.shop.shop_general import GeneralShop
from module.shop.shop_guild import GuildShop
from module.shop.shop_medal import MedalShop
from module.shop.shop_merit import MeritShop
from module.shop.ui import ShopUI
from module.config.utils import server_timezone


class RewardShop(GachaUI, ShopUI, GeneralShop, GuildShop, MedalShop, MeritShop):
    def _shop_visit(self, shop_type='general'):
        """
        Helper func to determine whether worth visiting and browsing the shop

        Args:
            shop_type (string): String assists with validating config

        Returns:
            bool: If worth visiting, empty selection means should not visit
        """
        try:
            selection = getattr(self.config, f'{shop_type.capitalize()}Shop_Filter')
        except AttributeError:
            logger.warning(f'_shop_visit --> Missing Config {shop_type.capitalize()}Shop_Filter')
            return False

        if not selection.strip():
            return False
        return True

    def _shop_repeat(self, shop_type='general'):
        """
        Common helper func for general, guild, and merit shops
        """
        try:
            selection = getattr(self.config, f'{shop_type.capitalize()}Shop_Filter')
            refresh = getattr(self.config, f'{shop_type.capitalize()}Shop_Refresh')
        except AttributeError:
            logger.warning(f'_shop_repeat --> Missing necessary Configs')
            return

        for _ in range(2):
            self.shop_buy(shop_type=shop_type, selection=selection)
            if refresh and self.shop_refresh():
                continue
            break
    
    def shop_skip_check(self):
        local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tz = timezone(timedelta(hours=server_timezone())) 
        server_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        #logger.info(f'local_time = {local_time}')
        #logger.info(f'server_time = {server_time}')
        local_time = datetime.strptime(local_time, '%Y-%m-%d %H:%M:%S')
        server_time = datetime.strptime(server_time, '%Y-%m-%d %H:%M:%S')
        result = self.config.Scheduler_NextRun + (server_time - local_time)
        if result.hour == 0:
            return True
        return False
        
    def run(self):
        self.ui_goto_shop()

        if self._shop_visit('general'):
            logger.hr('General shop', level=1)
            if self.shop_bottom_navbar_ensure(left=5):
                self._shop_repeat(shop_type='general')

        if shop_skip_check() == True:
            if self._shop_visit('merit'):
                logger.hr('Merit shop', level=1)
                if self.shop_bottom_navbar_ensure(left=4):
                    self._shop_repeat(shop_type='merit')

            if self._shop_visit('guild'):
                logger.hr('Guild shop', level=1)
                if self.shop_bottom_navbar_ensure(left=1):
                    self._shop_repeat(shop_type='guild')

            if self._shop_visit('medal'):
                logger.hr('Medal shop', level=1)
                self.ui_goto_gacha()
                if self.gacha_side_navbar_ensure(bottom=2):
                    for _ in [1, 2]:
                        if self.gacha_bottom_navbar_ensure(left=_, is_build=False):
                            self.shop_buy(shop_type='medal',
                                          selection=self.config.MedalShop_Filter)
                        else:
                            logger.warning('Failed to arrive at expected '
                                           'build interface for medal exchanges, '
                                           f'left={_}, try again next time')
        else:
            logger.info(f'Next run {self.config.Scheduler_NextRun} is not at 00:00, skip merit, guild and medal shops')

        self.config.task_delay(server_update=True)
