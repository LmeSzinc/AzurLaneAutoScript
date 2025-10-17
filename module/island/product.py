from module.template.assets import *

PRODUCT_INDEX_MAP = {
    'TEMPLATE_ISLAND_MINING': {
        '0': 'disabled',
        '1': 'coal',
        '2': 'copper',
        '3': 'aluminum',
        '4': 'iron',
        '5': 'sulfur',
        '6': 'silver',
    },
    'TEMPLATE_ISLAND_LUMBERING': {
        '0': 'disabled',
        '1': 'raw',
        '2': 'useful',
        '3': 'premium',
        '4': 'elegant',
    },
    'TEMPLATE_ISLAND_RANCH': {
        '0': 'disabled',
        '1': 'eggs',
        '2': 'pork',
        '3': 'milk',
        '4': 'wool',
    },
}

PRODUCT_TEMPLATE_ICON_MAP = {
    'coal': TEMPLATE_ISLAND_ORE_T1,
    'copper': TEMPLATE_ISLAND_ORE_T2,
    'aluminum': TEMPLATE_ISLAND_ORE_T3,
    'iron': TEMPLATE_ISLAND_ORE_T4,
    # 'sulfur': TEMPLATE_ISLAND_ORE_T5,
    # 'silver': TEMPLATE_ISLAND_ORE_T6,
    'raw': TEMPLATE_ISLAND_WOOD_T1,
    'useful': TEMPLATE_ISLAND_WOOD_T2,
    'premium': TEMPLATE_ISLAND_WOOD_T3,
    # 'elegant': TEMPLATE_ISLAND_WOOD_T4,
}