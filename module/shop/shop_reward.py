from module.gacha.ui import GachaUI
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
            selection = getattr(self.config, f'SHOP_{shop_type.upper()}_SELECTION')
        except AttributeError:
            logger.warning(f'_shop_visit --> Missing Config SHOP_{shop_type.upper()}_SELECTION')
            return False

        if not selection.strip():
            return False
        return True

    def _shop_record_since(self, shop_type_list):
        """
        Helper func to scan shop records
        determining whether need to transition
        to pages

        Args:
            shop_type_list (list):
                list of strings, each
                representing shop to
                check against

        Returns:
            dict: shop (key)  --> bool
                  If shop(s) should be page transitioned to
        """
        shop_records = {}
        for shop_type in shop_type_list:
            shop_records[shop_type] = False
            try:
                since = globals()[f'RECORD_SHOP_{shop_type.upper()}_SINCE']
                option = globals()[f'RECORD_SHOP_{shop_type.upper()}_OPTION']
            except KeyError:
                logger.warning('_shop_record_since --> Missing shop records '
                               f'for shop {shop_type} to verify')
                continue

            if not self.config.record_executed_since(option=option, since=since):
                if self._shop_visit(shop_type=shop_type):
                    shop_records[shop_type] = True

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
            return

        for _ in range(2):
            self.shop_buy(shop_type=shop_type, selection=selection)
            if refresh and self.shop_refresh():
                continue
            break

    def shop_run(self):
        """
        Runs shop browse operations

        Returns:
            bool: If shop attempted to run
                  thereby transition to respective
                  pages. If no transition took place,
                  then did not run
        """
        shop_ran = False
        shop_records = self._shop_record_since(['general', 'guild', 'merit'])
        if any(shop_records.values()):
            shop_ran = True
            if not self.ui_goto_shop():
                logger.warning('Failed to arrive at expected shop '
                               'interface, try again next time')
                return shop_ran

            if shop_records['general']:
                if self.shop_bottom_navbar_ensure(left=5):
                    self._shop_repeat(shop_type='general')
                    self.config.record_save(option=RECORD_SHOP_GENERAL_OPTION)

            if shop_records['merit']:
                if self.shop_bottom_navbar_ensure(left=4):
                    self._shop_repeat(shop_type='merit')
                    self.config.record_save(option=RECORD_SHOP_MERIT_OPTION)

            if shop_records['guild']:
                if self.shop_bottom_navbar_ensure(left=1):
                    self._shop_repeat(shop_type='guild')
                    self.config.record_save(option=RECORD_SHOP_GUILD_OPTION)

        shop_records = self._shop_record_since(['medal'])
        if any(shop_records.values()):
            shop_ran = True
            if shop_records['medal']:
                self.ui_goto_gacha()

                record_save = True
                if not self.gacha_side_navbar_ensure(bottom=2):
                    return shop_ran

                for _ in range(1, 3):
                    if self.gacha_bottom_navbar_ensure(left=_, is_build=False):
                        self.shop_buy(shop_type='medal',
                                      selection=self.config.SHOP_MEDAL_SELECTION)
                    else:
                        logger.warning('Failed to arrive at expected '
                                       'build interface for medal exchanges, '
                                       f'left={_}, try again next time')
                        record_save = False
                if record_save:
                    self.config.record_save(option=RECORD_SHOP_MEDAL_OPTION)

        return shop_ran

    def handle_shop(self):
        """
        Handles shop browse operations
        """
        if not self.config.ENABLE_SHOP_BUY:
            return False

        if self.shop_run():
            self.ui_goto_main()

        return True
