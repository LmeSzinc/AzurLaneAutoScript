import re
from module.base.filter import Filter

FILTER_REGEX = re.compile(
    '(cube|drill|chip|array|pry|dr|box|bulin|book|food|plate|retrofit)'

    '(neptune|monarch|ibuki|izumo|roon|saintlouis'
    '|seattle|georgia|kitakaze|azuma|friedrich'
    '|gascogne|champagne|cheshire|drake|mainz|odin'
    '|anchorage|hakuryu|agir|august|marcopolo'
    '|red|blue|yellow'
    '|general|gun|torpedo|antiair|plane'
    '|dd|cl|bb|cv)?'

    '(s[1-4]|t[1-6])?',
    flags=re.IGNORECASE)
FILTER_ATTR = ('group', 'sub_genre', 'tier')
FILTER = Filter(FILTER_REGEX, FILTER_ATTR)
