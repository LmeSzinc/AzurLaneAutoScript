import re
from module.config.config_generated import GeneratedConfig

from module.os_handler.preset import *
from module.base.filter import Filter

FILTER_REGEX = re.compile(
    '^(actionpoint|crystallizedheatresistantsteel|developmentmaterial'
    '|energystoragedevice|geardesignplan|gearpart|logger|metaredbook'
    '|nanoceramicalloy|neuroplasticprostheticarm|ordnancetestingreport'
    '|platerandom|purplecoins|repairpack|supercavitationgenerator|tuningsample'
    '|tuning)'

    '(20|50|100|prototype|specialized|abyssal|obscure|full2|full|triple2|triple|2'
    '|combat|offence|survival)?'

    '(t[1-6])?$',
    flags=re.IGNORECASE)
FILTER_ATTR = ('group', 'sub_genre', 'tier')
FILTER = Filter(FILTER_REGEX, FILTER_ATTR)


class Selector():
    prise_yellow_coin = 0
    prise_purple_coin = 0

    def clear_prise(self):
        self.prise_yellow_coin = 0
        self.prise_purple_coin = 0

    def pretreatment(self, items) -> list:
        """
        Pretreatment items.

        Args:
            items:

        Returns:
            list[Item]:
        """
        _items = []
        for item in items:
            item.group, item.sub_genre, item.tier = None, None, None
            result = re.search(FILTER_REGEX, item.name.lower())
            if result:
                item.group, item.sub_genre, item.tier = [group.lower()
                                                         if group is not None else None
                                                         for group in result.groups()]
                _items.append(item)

        return _items

    def enough_coins_in_port(self, item) -> bool:
        """
        Check if there are enough coins to buy the item.

        Args:
            item:

        Returns:
            bool: True if there are enough coins.
        """
        if item.cost == 'YellowCoins' and self.prise_yellow_coin + item.price <= \
                self._shop_yellow_coins - 100000 if self.is_cl1_enabled else 35000:
            self.prise_yellow_coin += item.price
            return True
        if item.cost == 'PurpleCoins' and self.prise_purple_coin + item.price <= self._shop_purple_coins:
            self.prise_purple_coin += item.price
            return True

        return False

    def enough_coins_in_akashi(self, item) -> bool:
        """
        Check if there are enough coins to buy the item.

        Args:
            item:

        Returns:
            bool: True if there are enough coins.
        """
        if item.cost == 'YellowCoins' and self.prise_yellow_coin + item.price <= self._shop_yellow_coins:
            self.prise_yellow_coin += item.price
            return True
        if item.cost == 'PurpleCoins' and self.prise_purple_coin + item.price <= self._shop_purple_coins:
            self.prise_purple_coin += item.price
            return True

        return False

    def check_cl1_purple_coins(self, item) -> bool:
        """
        Check if cl1 is enable and item name is PurpleCoins.

        Args:
            item:

        Returns:
            bool: False if cl1 is enable and item name is PurpleCoins.
        """
        return not (self.is_cl1_enabled and item.name == 'PurpleCoins')

    def items_filter_in_akashi_shop(self, items) -> list:
        """
        Returns items that can be bought.

        Args:
            items: Irems to be filtered.

        Returns:
            list[Item]:
        """
        self.clear_prise()
        items = self.pretreatment(items)
        parser = self.config.OpsiGeneral_AkashiShopFilter
        if not parser.strip():
            parser = GeneratedConfig.OpsiGeneral_AkashiShopFilter
        FILTER.load(parser)
        return FILTER.apply(items, func=[self.check_cl1_purple_coins, self.enough_coins_in_akashi])

    def items_filter_in_os_shop(self, items) -> list:
        """
        Returns items that can be bought.

        Args:
            items: Items to be filtered.

        Returns:
            list[Item]:
        """
        self.clear_prise()
        items = self.pretreatment(items)
        preset = self.config.OpsiShop_PresetFilter
        parser = ''
        if preset == 'custom':
            parser = self.config.OpsiShop_CustomFilter
            if not parser.strip():
                parser = OS_SHOP[GeneratedConfig.OpsiShop_PresetFilter]
        else:
            parser = OS_SHOP[preset]
        FILTER.load(parser)
        return FILTER.applys(items, funcs=[self.enough_coins_in_port, self.check_cl1_purple_coins])
