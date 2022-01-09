import re
from module.base.filter import Filter

FILTER_REGEX = re.compile(
    '(cube|drill|chip|array|pr|dr|box|bulin|book|food|plate|retrofit)'

    '(neptune|monarch|ibuki|izumo|roon|saintlouis'
    '|seattle|georgia|kitakaze|azuma|friedrich'
    '|gascogne|champagne|cheshire|drake|mainz|odin'
    '|anchorage|hakuryu|agir|august|marcopolo'
    '|red|blue|yellow'
    '|general|gun|torpedo|antiair|plane'
    '|dd|cl|bb|cv)?'

    '(s[1-4]|t[1-6])?')
FILTER_ATTR = ('group', 'sub_genre', 'tier')
FILTER = Filter(FILTER_REGEX, FILTER_ATTR)

# PR/DR Ship to Series #
# misc keys for hashing
BP_SERIES = {
    'neptune': 1,
    'monarch': 1,
    'ibuki': 1,
    'izumo': 1,
    'roon': 1,
    'saintlouis': 1,
    'seattle': 2,
    'georgia': 2,
    'kitakaze': 2,
    'gascogne': 2,
    'azuma': 2,
    'friedrich': 2,
    'cheshire': 3,
    'mainz': 3,
    'odin': 3,
    'champagne': 3,
    'drake': 3,
    'anchorage': 4,
    'august': 4,
    'marcopolo': 4,
    'agir': 4,
    'hakuryu': 4,
    '1': 1,
    '2': 2,
    '3': 3,
    '4': 4,
    '': '',
}

# Known items with no tiers
ITEM_NO_TIERS = [
    'Chip',
    'Array',
    'Drill',
    'Cube',
]