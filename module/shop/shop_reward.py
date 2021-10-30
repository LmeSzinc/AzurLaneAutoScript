from module.config.utils import get_server_last_update
from module.gacha.ui import GachaUI
from module.logger import logger
from module.shop.shop_general import GeneralShop
from module.shop.shop_guild import GuildShop
from module.shop.shop_medal import MedalShop
from module.shop.shop_merit import MeritShop
from module.shop.ui import ShopUI


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

    def run_frequent(self):
        self.ui_goto_shop()

        if self._shop_visit('general'):
            logger.hr('General shop', level=1)
            if self.shop_bottom_navbar_ensure(left=5):
                self._shop_repeat(shop_type='general')

        self.config.task_delay(server_update=True)

    def run_once(self):
        self.ui_goto_shop()

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

        self.config.task_delay(server_update=True)