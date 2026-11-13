"""Shared island-production worker-pool configuration.

Unlike restaurant, which pins specific named waitresses to specific slots
(because the waitress identity determines a fixed sales bonus), production
slots don't need deterministic identity: the automation already OCRs the
finish time, so it never needs to know *which* character produced *what*
bonus. What it does need is a stamina-aware way to opportunistically staff
open slots from a ranked pool of characters, falling back to Workerjuu (no
stamina limit) when the pool is exhausted or everyone's resting.

Worker pools are scoped per production place (mine, ranch, cafe, etc.), and
further split per-slot for Ranch (102), since each ranch slot is a distinct,
fixed product (chicken/pig/cow/sheep) rather than an interchangeable general
slot. A character configured for one pool is not drafted into another,
except when that other place is fully idle for the day (the planner assigned
it zero production), in which case its pool is folded in as a lower-priority
fallback.

A place or slot without any pool keeps the upstream behaviour: any free
character within the stamina window, then Workerjuu. Whether to skip named
workers entirely is decided by IslandProduction.UseWorkerjuuByDefault.

This module has no device or UI dependencies, matching restaurant_config.py.
"""

from module.exception import RequestHumanTakeover
from module.island_handler.restaurant_config import get_blacklisted_waitresses
from module.logger import logger

WORKER_WORKERJUU = 'Workerjuu'

ISLAND_PRODUCTION_WORKER_CONFIG_PREFIX = 'IslandProduction.IslandProduction.'

# Maps production place_id (as returned by get_production_codename) to its
# WorkerPool config key under IslandProduction.IslandProduction. Ranch (102)
# is intentionally omitted here - see SLOT_POOL_KEYS / PLACE_TO_SLOT_POOLS.
PLACE_POOL_KEYS = {
    101: 'WorkerPoolField',
    201: 'WorkerPoolFishery',
    401: 'WorkerPoolMine',
    402: 'WorkerPoolWood',
    501: 'WorkerPoolOrchard',
    502: 'WorkerPoolNursery',
    601: 'WorkerPoolKoi',
    602: 'WorkerPoolBear',
    603: 'WorkerPoolEatery',
    604: 'WorkerPoolGrill',
    703: 'WorkerPoolLumber',
    704: 'WorkerPoolMachinery',
    705: 'WorkerPoolElectronic',
    706: 'WorkerPoolCrafts',
    901: 'WorkerPoolCafe',
}

# Slots whose worker pool is defined individually rather than per-place.
SLOT_POOL_KEYS = {
    9031: 'WorkerPoolRanchChicken',
    9032: 'WorkerPoolRanchPig',
    9033: 'WorkerPoolRanchCow',
    9034: 'WorkerPoolRanchSheep',
}

# Places whose pool is defined per-slot (see SLOT_POOL_KEYS) rather than
# per-place. Used when a pool is needed without a specific slot_id, e.g.
# when this place's pool is being borrowed by another idle place.
PLACE_TO_SLOT_POOLS = {
    102: [9031, 9032, 9033, 9034],
}

RESERVED_CHARACTERS_KEY = f'{ISLAND_PRODUCTION_WORKER_CONFIG_PREFIX}ReservedCharacters'


def _parse_name_list(text):
    """Parse a human-typed, comma-separated list of character names.

    Accepts plain "Saratoga, Chen_Hai, Laffey" and tolerates being wrapped
    in JSON-style brackets/quotes left over from an earlier config format,
    as well as trailing commas and stray whitespace, so hand-edited or
    previously-saved values both parse without raising.

    Names are the template file names in assets/island/character, e.g. Chen_Hai.
    """
    text = (text or '').strip()
    if text.startswith('[') and text.endswith(']'):
        text = text[1:-1]
    names = []
    for part in text.split(','):
        name = part.strip().strip('"').strip("'").strip()
        if name:
            names.append(name)
    return names


def get_worker_pool(config, place_id, slot_id=None):
    """Return the priority-ordered list of character names configured for
    this production place or slot.

    Args:
        config: Alas config object.
        place_id (int): Production place codename, e.g. 401 for mine.
        slot_id (int, optional): Specific slot id. Only meaningful for
            places whose pool is defined per-slot (currently only Ranch,
            102) - ignored for every other place.

    Returns:
        list[str]: Highest priority first. Empty list means no pool configured.
    """
    if slot_id is not None and slot_id in SLOT_POOL_KEYS:
        key = SLOT_POOL_KEYS[slot_id]
    elif place_id in PLACE_TO_SLOT_POOLS:
        # No specific slot given for a per-slot place (e.g. borrowing its
        # pool while idle) - union all of its sub-pools instead.
        names = []
        seen = set()
        for sub_slot_id in PLACE_TO_SLOT_POOLS[place_id]:
            for name in get_worker_pool(config, place_id, slot_id=sub_slot_id):
                if name not in seen:
                    names.append(name)
                    seen.add(name)
        return names
    else:
        key = PLACE_POOL_KEYS.get(place_id)

    if key is None:
        logger.warning(f'No WorkerPool config mapped for place_id {place_id} slot_id {slot_id}, defaulting to no pool')
        return []
    text = config.cross_get(f'{ISLAND_PRODUCTION_WORKER_CONFIG_PREFIX}{key}', default='')
    return _parse_name_list(text)


def get_idle_place_ids(config):
    """Return place_ids the production planner determined are fully idle
    (zero planned production) for the current cycle.

    Args:
        config: Alas config object.

    Returns:
        list[int]
    """
    return config.cross_get("IslandProductionPlanner.Storage.Storage.IdlePlaceIds", default=[])


def get_reserved_characters(config):
    """Characters production must never use, regardless of time of day or
    anything else. A blunt, explicit opt-in for reserving specific named
    characters (e.g. for gathering) - no prediction, no timing.
    """
    text = config.cross_get(RESERVED_CHARACTERS_KEY, default='')
    return set(_parse_name_list(text))


def get_unavailable_characters(config):
    """Characters production must not use right now: named waitresses of
    restaurants that have not run since the daily reset, plus the manually
    reserved characters.
    """
    return get_blacklisted_waitresses(config) | get_reserved_characters(config)


def get_effective_worker_pool(config, place_id, slot_id=None):
    """Own pool first (priority order preserved), then pools borrowed from
    places that are fully idle for the day, deduped. Characters currently
    reserved for restaurant duty, or manually reserved, are excluded
    entirely.

    Args:
        config: Alas config object.
        place_id (int): Production place codename.
        slot_id (int, optional): Specific slot id, for per-slot places (Ranch).

    Returns:
        list[str]: Highest priority first. Empty list means no pool.
    """
    blacklist = get_unavailable_characters(config)
    combined = [name for name in get_worker_pool(config, place_id, slot_id=slot_id) if name not in blacklist]
    seen = set(combined)
    for other_id in sorted(p for p in get_idle_place_ids(config) if p != place_id):
        for name in get_worker_pool(config, other_id):
            if name not in seen and name not in blacklist:
                combined.append(name)
                seen.add(name)
    return combined


def get_min_stamina(config):
    """Minimum stamina (emotion) required before a character will be assigned
    to a production slot from a worker pool. Set this above 1 to reserve more
    stamina for other tasks; a floor below 1 is not honored, since a
    0-stamina character cannot start even a single batch (confirmed: 100%
    failure rate in testing).
    """
    value = config.cross_get(f'{ISLAND_PRODUCTION_WORKER_CONFIG_PREFIX}MinStaminaToAssign', default=0)
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise RequestHumanTakeover(f'IslandProduction.MinStaminaToAssign must be an integer, got: {value}')
    return max(value, 1)
