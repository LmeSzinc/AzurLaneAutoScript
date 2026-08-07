"""Shared restaurant configuration and waitress helpers.

This module intentionally has no device or UI dependencies so it can be used by
the restaurant runner, IslandBusiness, the production planner, and config
migration code alike.
"""

from collections import OrderedDict

from module.exception import RequestHumanTakeover


WAITRESS_NONE = 'none'
WAITRESS_ANY = 'any'


# Keep the option/bonus data in one place.  ``waitress_effects`` values are
# ``(capacity_delta, sales_bonus)`` and bonuses are only applied for explicitly
# selected named waitresses, matching the previous behaviour.
RESTAURANT_CONFIG = OrderedDict({
    601: {
        'name': 'Koi',
        'grade_key': 'KoiGrade',
        'waitress_keys': ('KoiWaitress1', 'KoiWaitress2'),
        'legacy_waitress_key': 'KoiWaitress',
        'menu_key': 'KoiMenu',
        'waitress_options': ('Chao_Ho', 'Chang_Feng'),
        'waitress_effects': {
            'Chao_Ho': (1, 0.10),
            'Chang_Feng': (1, 0),
        },
    },
    602: {
        'name': 'Bear',
        'grade_key': 'BearGrade',
        'waitress_keys': ('BearWaitress1', 'BearWaitress2'),
        'legacy_waitress_key': 'BearWaitress',
        'menu_key': 'BearMenu',
        'waitress_options': ('Cheshire', 'Chang_Feng'),
        'waitress_effects': {
            'Cheshire': (1, 0.05),
            'Chang_Feng': (1, 0),
        },
    },
    603: {
        'name': 'Eatery',
        'grade_key': 'EateryGrade',
        'waitress_keys': ('EateryWaitress1', 'EateryWaitress2'),
        'legacy_waitress_key': 'EateryWaitress',
        'menu_key': 'EateryMenu',
        'waitress_options': ('Helena', 'Prinz_Eugen', 'Chang_Feng'),
        'waitress_effects': {
            'Helena': (1, 0.10),
            'Prinz_Eugen': (0, 0.10),
            'Chang_Feng': (1, 0),
        },
    },
    604: {
        'name': 'Grill',
        'grade_key': 'GrillGrade',
        'waitress_keys': ('GrillWaitress1', 'GrillWaitress2'),
        'legacy_waitress_key': 'GrillWaitress',
        'menu_key': 'GrillMenu',
        'waitress_options': ('August_von_Parseval', 'Prinz_Eugen', 'Chang_Feng'),
        'waitress_effects': {
            'August_von_Parseval': (1, 0.10),
            'Prinz_Eugen': (0, 0.10),
            'Chang_Feng': (1, 0),
        },
    },
    901: {
        'name': 'Cafe',
        'grade_key': 'CafeGrade',
        'waitress_keys': ('CafeWaitress1', 'CafeWaitress2'),
        'legacy_waitress_key': 'CafeWaitress',
        'menu_key': 'CafeMenu',
        'waitress_options': ('Cheshire', 'Belfast', 'Chang_Feng'),
        'waitress_effects': {
            'Cheshire': (1, 0.05),
            'Belfast': (0, 0.10),
            'Chang_Feng': (1, 0),
        },
    },
})

RESTAURANT_IDS = tuple(RESTAURANT_CONFIG.keys())
ISLAND_RESTAURANT_CONFIG_PREFIX = 'IslandBusiness.IslandRestaurant.'


def get_restaurant_config(restaurant_id):
    return RESTAURANT_CONFIG[restaurant_id]


def get_config_key(restaurant_id, key):
    return ISLAND_RESTAURANT_CONFIG_PREFIX + key


def get_waitress_options(restaurant_id):
    return (WAITRESS_NONE, WAITRESS_ANY) + tuple(
        get_restaurant_config(restaurant_id)['waitress_options']
    )


def _waitress_sort_key(restaurant_id, value):
    config = get_restaurant_config(restaurant_id)
    if value == WAITRESS_NONE:
        return (2, 0)
    if value == WAITRESS_ANY:
        return (1, 0)
    try:
        index = config['waitress_options'].index(value)
    except ValueError:
        index = len(config['waitress_options'])
    return (0, index)


def normalize_waitress_slots(restaurant_id, values):
    """Validate and return a canonical, unordered pair of waitress values.

    Slot order is canonicalized because the two slots are unordered. Invalid
    combinations are not repaired: they require human intervention.
    """
    allowed = set(get_waitress_options(restaurant_id))
    values = list(values or [])
    cleaned = []
    seen_named = set()
    for value in values:
        if value is None:
            value = WAITRESS_NONE
        if value not in allowed:
            raise RequestHumanTakeover(
                f'Invalid waitress value for restaurant {restaurant_id}: {value}'
            )
        if value not in (WAITRESS_NONE, WAITRESS_ANY):
            if value in seen_named:
                raise RequestHumanTakeover(
                    f'Duplicate named waitress for restaurant {restaurant_id}: {value}'
                )
            seen_named.add(value)
        cleaned.append(value)

    if len(cleaned) > 2:
        raise RequestHumanTakeover(
            f'Restaurant {restaurant_id} has more than two waitress slots'
        )

    cleaned.sort(key=lambda value: _waitress_sort_key(restaurant_id, value))
    cleaned.extend([WAITRESS_NONE] * (2 - len(cleaned)))
    return tuple(cleaned)


def get_waitress_slots(config, restaurant_id):
    config_data = get_restaurant_config(restaurant_id)
    values = [
        config.cross_get(get_config_key(restaurant_id, key), default=None)
        for key in config_data['waitress_keys']
    ]
    return normalize_waitress_slots(restaurant_id, values)


def is_restaurant_enabled(slots):
    return any(value != WAITRESS_NONE for value in slots)


def get_selected_named_waitresses(slots):
    return {
        value for value in slots
        if value not in (WAITRESS_NONE, WAITRESS_ANY)
    }


def get_waitress_effect(restaurant_id, slots):
    slots = normalize_waitress_slots(restaurant_id, slots)
    capacity_delta = 0
    sales_bonus = 0
    effects = get_restaurant_config(restaurant_id)['waitress_effects']
    for waitress in get_selected_named_waitresses(slots):
        capacity, sales = effects.get(waitress, (0, 0))
        capacity_delta += capacity
        sales_bonus += sales
    return capacity_delta, sales_bonus


def legacy_waitress_to_slots(value, restaurant_id):
    """Convert an old ``name+name`` waitress value into two new slots."""
    if not isinstance(value, str):
        values = []
    else:
        values = value.split('+')
    return normalize_waitress_slots(restaurant_id, values)
