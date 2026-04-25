import re

from module.base.filter import Filter

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

    '(s[1-8]|t[1-6])?$'
)
FILTER_ATTR = ('group', 'sub_genre', 'tier')
FILTER = Filter(FILTER_REGEX, FILTER_ATTR)


EVENT_SHOP_PRESET_FILTER = {
    'all': """
        EquipUR > EquipSSR > Cube > GachaTicket
        > Array > Chip > CatT3 
        > Meta > SkinBox
        > Oil > Coin > Medal > ExpBookT1 > FoodT1
        > DR > PR
        > AugmentCore > AugmentEnhanceT2 > AugmentChangeT2 > AugmentChangeT1
        > CatT2 > CatT1 > PlateGeneralT3 > PlateT3 > BoxT4
        > ShipSSR
    """,
}