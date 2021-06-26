from module.build.ui import BuildUI
from module.logger import logger
from module.shop.shop_general import GeneralShop
from module.shop.shop_guild import GuildShop
from module.shop.shop_medal import MedalShop
from module.shop.shop_merit import MeritShop
from module.shop.ui import ShopUI

RECORD_SHOP_GENERAL_OPTION = ('RewardRecord', 'shop_general')
RECORD_SHOP_GENERAL_SINCE = (0, 12, 18,)
RECORD_SHOP_GUILD_OPTION = ('RewardRecord', 'shop_guild')
RECORD_SHOP_GUILD_SINCE = (0,)
RECORD_SHOP_MEDAL_OPTION = ('RewardRecord', 'shop_medal')
RECORD_SHOP_MEDAL_SINCE = (0,)
RECORD_SHOP_MERIT_OPTION = ('RewardRecord', 'shop_merit')
RECORD_SHOP_MERIT_SINCE = (0,)

SHOP_TYPE_LIST = ['general', 'guild', 'medal', 'merit']


class RewardShop(BuildUI, ShopUI, GeneralShop, GuildShop, MedalShop, MeritShop):
    def _shop_visit(self, shop_type='general'):
        """
        Helper func to determine whether worth visiting and browsing the shop

        Args:
            shop_type (string): String assists with validating config

        Returns:
            bool: If worth visiting, empty selection means should not visit
        """
        try:
            selection = getattr(self.config, f'SHOP_{shop_type.upper()}_SELECTION')
        except AttributeError:
            logger.warning(f'_shop_visit --> Missing Config SHOP_{shop_type.upper()}_SELECTION')
            return False

        if not selection.strip():
            return False
        return True

    def _shop_record_since(self):
        """
        Helper func to scan shop records
        determining whether need to transition
        to pages

        Returns:
            bool: If shop_run successful
        """
        shop_records = {}
        for shop_type in SHOP_TYPE_LIST:
            try:
                since = globals()[f'RECORD_SHOP_{shop_type.upper()}_SINCE']
                option = globals()[f'RECORD_SHOP_{shop_type.upper()}_OPTION']
            except KeyError:
                logger.warning(f'_shop_record_since --> Missing shop records to verify')
                continue

            result = False
            if not self.config.record_executed_since(option=option, since=since):
                if self._shop_visit(shop_type=shop_type):
                    result = True
                self.config.record_save(option=option)
            shop_records[shop_type] = result

        return shop_records


    def _shop_repeat(self, shop_type='general'):
        """
        Common helper func for general, guild, and merit shops
        """
        try:
            selection = getattr(self.config, f'SHOP_{shop_type.upper()}_SELECTION')
            refresh = getattr(self.config, f'ENABLE_SHOP_{shop_type.upper()}_REFRESH')
        except AttributeError:
            logger.warning(f'_shop_repeat --> Missing necessary Configs')

        for _ in range(2):
            self.shop_buy(shop_type=shop_type, selection=selection)
            if refresh:
                self.shop_refresh()
            else:
                break

    def shop_run(self):
        """
        Runs shop browse operations

        Returns:
            bool: If shop_run successful
        """
        shop_records = self._shop_record_since()
        if not any(shop_records.values()):
            logger.info('No shops to visit according to records')
            return True

        if not self.ui_goto_shop():
            logger.warning('Failed to arrive at expected shop interface, try again next time')
            self.ui_goto_main()
            return False

        if shop_records['general']:
            self.shop_bottombar_ensure(1)
            self._shop_repeat(shop_type='general')

        if shop_records['merit']:
            self.shop_bottombar_ensure(2)
            self._shop_repeat(shop_type='merit')

        if shop_records['guild']:
            self.shop_bottombar_ensure(5)
            self._shop_repeat(shop_type='guild')

        if shop_records['medal']:
            for _ in range(1, 3):
                if self.ui_goto_build(2, _):
                    self.shop_buy(shop_type='medal', selection=self.config.SHOP_MEDAL_SELECTION)

        self.ui_goto_main()
        return True

    def handle_shop(self):
        """
        Handles shop browse operations
        """
        if not self.config.ENABLE_SHOP_BROWSE:
            return False

        return self.shop_run()
