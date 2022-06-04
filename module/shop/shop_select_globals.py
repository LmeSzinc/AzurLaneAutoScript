from module.base.button import ButtonGrid

# Known Secondary Grid Sizes
SELECT_GRID_3X1 = ButtonGrid(
    origin=(412, 258), delta=(158, 0), button_shape=(119, 19), grid_shape=(3, 1),
    name='SHOP_SELECT_GRID_3X1')

SELECT_GRID_4X1 = ButtonGrid(
    origin=(334, 258), delta=(158, 0), button_shape=(119, 19), grid_shape=(4, 1),
    name='SHOP_SELECT_GRID_4X1')

SELECT_GRID_5X1 = ButtonGrid(
    origin=(256, 258), delta=(158, 0), button_shape=(119, 19), grid_shape=(5, 1),
    name='SHOP_SELECT_GRID_5X1')

SELECT_GRID_6X1 = ButtonGrid(
    origin=(176, 258), delta=(158, 0), button_shape=(119, 19), grid_shape=(6, 1),
    name='SHOP_SELECT_GRID_6X1')

# Consolidated Select Item Information Map
# Applicable shops (Guild and Medal)
# Placeholder entry 'DR'; not valid atm
SELECT_ITEM_INFO_MAP = {
    'book': {
        'grid': SELECT_GRID_3X1,
        'choices': {
            'red': 0,
            'blue': 1,
            'yellow': 2,
        },
    },
    'box': {
        'grid': SELECT_GRID_4X1,
        'choices': {
            'eagle': 0,
            'royal': 1,
            'sakura': 2,
            'ironblood': 3,
        },
    },
    'retrofit': {
        'grid': SELECT_GRID_4X1,
        'choices': {
            'dd': 0,
            'cl': 1,
            'bb': 2,
            'cv': 3,
        },
    },
    'plate': {
        'grid': SELECT_GRID_5X1,
        'choices': {
            'general': 0,
            'gun': 1,
            'torpedo': 2,
            'antiair': 3,
            'plane': 4,
        },
    },
    'pr': {
        'grid': {
            's1': SELECT_GRID_6X1,
            's2': SELECT_GRID_4X1,
            's3': SELECT_GRID_4X1,
            's4': SELECT_GRID_3X1,
        },
        'choices': {
            'neptune': 0,
            'monarch': 1,
            'ibuki': 2,
            'izumo': 3,
            'roon': 4,
            'saintlouis': 5,
            'seattle': 0,
            'georgia': 1,
            'kitakaze': 2,
            'gascogne': 3,
            'cheshire': 0,
            'mainz': 1,
            'odin': 2,
            'champagne': 3,
            'anchorage': 0,
            'august': 1,
            'marcopolo': 2,
        },
    },
    'dr': {
        'grid': {
            's1': SELECT_GRID_3X1,
            's2': SELECT_GRID_3X1,
            's3': SELECT_GRID_3X1,
            's4': SELECT_GRID_3X1,
        },
        'choices': {
            'azuma': 0,
            'friedrich': 1,
            'drake': 0,
            'agir': 0,
            'hakuryu': 1,
        },
    },
}
