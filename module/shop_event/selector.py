import re

from module.base.filter import Filter
from module.config.config_generated import GeneratedConfig

FILTER_REGEX = re.compile(
    '^(ship|equip|pt|gachaticket'
    '|meta|skinbox'
    '|array|chip|cat|pr|dr'
    '|augment'
    '|cube|medal|expbook'
    '|box|plate|coin|oil|food'
    ')'

    '(ur|ssr'
    '|core|change|enhance'
    '|general|gun|torpedo|antiair|plane)?'

    '(s[1-7]|t[1-6])?$'
)
FILTER_ATTR = ('group', 'sub_genre', 'tier')
FILTER = Filter(FILTER_REGEX, FILTER_ATTR)


EVENT_SHOP = {
    'all': """
        EquipUR > EquipSSR > GachaTicket
        > DR > PR > Array > Chip > CatT3
        > Meta > SkinBox
        > Oil > Coin > FoodT1
        > AugmentCore > AugmentEnhanceT2 > AugmentChangeT2 > AugmentChangeT1
        > Cube > Medal > ExpBookT1
        > CatT2 > CatT1 > PlateGeneralT3 > PlateT3 > BoxT4
        > ShipSSR
    """,
}

class EventShopSelector:
    def items_get_items(self, items, name, cost="Pt"):
        _items = []
        for item in items:
            if item.name == name and item.cost == cost:
                _items.append(item)
        return _items

    def pretreatment(self, items):
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

    def items_filter_in_event_shop(self, items):
        items = self.pretreatment(items)
        preset = self.config.EventShop_PresetFilter
        parser = ''
        if preset == 'custom':
            parser = self.config.EventShop_CustomFilter
            if not parser.strip():
                parser = EVENT_SHOP[GeneratedConfig.EventShop_PresetFilter]
        else:
            parser = EVENT_SHOP[preset]
        FILTER.load(parser)
        return FILTER.apply(items)