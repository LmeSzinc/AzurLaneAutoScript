import re
from collections import defaultdict
from typing import Dict

import numpy as np
from yaml import safe_dump, safe_load

import module.config.server as server
from module.island.data import DIC_ISLAND_ITEM, DIC_ISLAND_SEASON_ORDER
from module.logger import logger


def normalize_item_name(name):
    return str(name).strip()


def normalize_item_id(item_id):
    if isinstance(item_id, (int, np.integer)):
        normalized_id = int(item_id)
        if normalized_id in DIC_ISLAND_ITEM:
            return normalized_id
        raise ValueError(f'Unknown item id: {item_id}')

    item_text = normalize_item_name(item_id)
    if not item_text:
        raise ValueError('Empty item key')

    if item_text.isdigit():
        normalized_id = int(item_text)
        if normalized_id in DIC_ISLAND_ITEM:
            return normalized_id
        raise ValueError(f'Unknown item id: {item_text}')

    match = re.match(r'^(.*)\((\d+)\)$', item_text)
    if match:
        normalized_id = int(match.group(2))
        if normalized_id in DIC_ISLAND_ITEM:
            return normalized_id
        raise ValueError(f'Unknown item id: {item_text}')

    for normalized_id, item_data in DIC_ISLAND_ITEM.items():
        if item_data['name'][server.server] == item_text:
            return normalized_id

    raise ValueError(f'Unknown item key: {item_text}')


def normalize_item_keys(items=None):
    if not items:
        return {}
    normalized = {}
    for raw_item_id, raw_value in items.items():
        item_id = normalize_item_id(raw_item_id)
        normalized[item_id] = raw_value
    return normalized


def item_name(item_id):
    return DIC_ISLAND_ITEM[item_id]['name'][server.server]


def item_export_key(item_id, use_item_name=False):
    if use_item_name:
        return f'{item_name(item_id)} ({item_id})'
    return item_id


def item_mapping_to_yaml(items, use_item_name=False):
    payload = {
        item_export_key(item_id, use_item_name=use_item_name): value
        for item_id, value in sorted(items.items())
    }
    return safe_dump(payload, allow_unicode=True, sort_keys=False)


def load_item_mapping(yaml_text=None, config_name='Items'):
    if not yaml_text:
        return {}
    items = safe_load(yaml_text)
    if not items:
        return {}
    if not isinstance(items, dict):
        raise ValueError(f'{config_name} must be a YAML mapping')
    return items


def load_reserve_items(reserve_items_yaml=None):
    return load_item_mapping(reserve_items_yaml, config_name='ReserveItems')


def load_hard_floor_items(hard_floor_items_yaml=None):
    return load_item_mapping(hard_floor_items_yaml, config_name='HardFloorItems')


def load_request_buffer_items(request_buffer_items_yaml=None):
    return load_item_mapping(request_buffer_items_yaml, config_name='RequestBufferItems')


def normalize_technology_status(technology_status=None):
    if not technology_status:
        return {}
    if not isinstance(technology_status, dict):
        raise ValueError('TechnologyStatus must be a YAML mapping')
    return {
        int(technology_id): bool(unlocked)
        for technology_id, unlocked in technology_status.items()
    }


def load_technology_status(technology_status=None):
    if not technology_status:
        return {}
    if not isinstance(technology_status, dict):
        technology_status = safe_load(technology_status)
    return normalize_technology_status(technology_status)


def normalize_item_needs(items=None, default_period=1):
    if not items:
        return {}
    requirements = defaultdict(list)
    for raw_item_id, raw_value in items.items():
        item_id = normalize_item_id(raw_item_id)
        if isinstance(raw_value, (list, tuple)) or (isinstance(raw_value, dict) and 'deadlines' in raw_value):
            requirements[item_id].extend(item_need_input_to_requirements(raw_value, default_period=default_period))
            continue
        elif isinstance(raw_value, dict):
            total_need_count = raw_value.get('count', 0)
            rate_per_day = raw_value.get('rate_per_day', 0)
            if rate_per_day:
                period = float(total_need_count) / float(rate_per_day)
            else:
                period = raw_value.get('period', raw_value.get('days', default_period))
        else:
            total_need_count = raw_value
            period = default_period
        total_need_count = int(total_need_count)
        period = float(period)
        if total_need_count <= 0 or period <= 0:
            continue
        requirements[item_id].append((total_need_count, period))
    return {
        item_id: build_item_need_data(item_requirements)
        for item_id, item_requirements in requirements.items()
    }


def normalize_reserve_items(reserve_items=None):
    return normalize_item_needs(reserve_items, default_period=1)


def merge_item_needs(*item_needs):
    requirements = defaultdict(list)
    for needs in item_needs:
        for item_id, data in needs.items():
            requirements[item_id].extend(item_need_data_to_requirements(data))
    return {
        item_id: build_item_need_data(item_requirements)
        for item_id, item_requirements in requirements.items()
    }


def build_item_need_data(requirements):
    period_counts = defaultdict(int)
    for count, period in requirements:
        count = int(count)
        period = float(period)
        if count <= 0 or period <= 0:
            continue
        period_counts[period] += count

    deadlines = []
    total_need_count = 0
    rate_per_day = 0.0
    for period, count in sorted(period_counts.items()):
        total_need_count += count
        rate_per_day = max(rate_per_day, total_need_count / period)
        deadlines.append({
            'count': total_need_count,
            'period': period,
        })

    if not deadlines:
        return {
            'total_need_count': 0,
            'period': 1,
            'rate_per_day': 0.0,
        }

    return {
        'total_need_count': total_need_count,
        'period': deadlines[-1]['period'],
        'rate_per_day': rate_per_day,
        'deadlines': deadlines,
    }


def item_need_data_to_requirements(data):
    deadlines = data.get('deadlines')
    if not deadlines:
        return [(data['total_need_count'], data['period'])]

    requirements = []
    previous_count = 0
    for deadline in sorted(deadlines, key=lambda x: x['period']):
        count = int(deadline.get('count', deadline.get('total_need_count', 0)))
        period = float(deadline.get('period', deadline.get('days', data['period'])))
        marginal_count = count - previous_count
        if marginal_count > 0:
            requirements.append((marginal_count, period))
        previous_count = max(previous_count, count)
    return requirements


def item_need_input_to_requirements(data, default_period=1):
    if isinstance(data, dict):
        entries = data.get('deadlines', [])
    else:
        entries = data
    requirements = []
    for deadline in entries:
        if isinstance(deadline, dict):
            count = deadline.get('count', deadline.get('total_need_count', 0))
            period = deadline.get('period', deadline.get('days', default_period))
        else:
            count = deadline
            period = default_period
        count = int(count)
        period = float(period)
        if count > 0 and period > 0:
            requirements.append((count, period))
    return requirements


def parse_item_need_deadlines(item_need, default_period=1):
    if not item_need:
        return []
    if isinstance(item_need, dict) and item_need.get('deadlines') and (
        'total_need_count' in item_need or 'rate_per_day' in item_need
    ):
        return [
            (
                int(deadline.get('count', deadline.get('total_need_count', 0))),
                float(deadline.get('period', deadline.get('days', item_need['period']))),
            )
            for deadline in sorted(item_need['deadlines'], key=lambda x: x['period'])
            if int(deadline.get('count', deadline.get('total_need_count', 0))) > 0
        ]

    if isinstance(item_need, (list, tuple)) or (isinstance(item_need, dict) and 'deadlines' in item_need):
        data = build_item_need_data(item_need_input_to_requirements(item_need, default_period=default_period))
        return [
            (deadline['count'], deadline['period'])
            for deadline in data.get('deadlines', [])
        ]

    if isinstance(item_need, dict):
        total_need_count = item_need.get('count', item_need.get('total_need_count', 0))
        period = item_need.get('period', item_need.get('days', default_period))
        rate_per_day = item_need.get('rate_per_day', 0)
        if rate_per_day:
            period = float(total_need_count) / float(rate_per_day)
    else:
        total_need_count = item_need
        period = default_period
    total_need_count = int(total_need_count)
    period = float(period)
    if total_need_count <= 0 or period <= 0:
        return []
    return [(total_need_count, period)]


def merge_task_target_reserve_items(reserve_items, task_target_items):
    return merge_item_needs(
        normalize_item_needs(reserve_items),
        normalize_item_needs(task_target_items, default_period=10),
    )


def get_stuck_season_order_requirements(stuck_order_id):
    stuck_order_id = normalize_stuck_season_order_id(stuck_order_id)
    if not stuck_order_id:
        return {}

    requirements = defaultdict(int)
    visited = set()
    order_id = stuck_order_id
    while order_id:
        if order_id in visited:
            logger.warning(f'Detected season order loop at order id {order_id}')
            break
        visited.add(order_id)
        order = DIC_ISLAND_SEASON_ORDER.get(order_id)
        if order is None:
            logger.warning(f'Cannot find stuck season order id {order_id}')
            break
        for item_id, count in order.get('request', {}).items():
            requirements[item_id] += count
        order_id = order.get('next_order', 0)
    return dict(requirements)


def normalize_stuck_season_order_id(stuck_order_id):
    try:
        stuck_order_id = int(stuck_order_id)
    except (TypeError, ValueError):
        logger.warning(f'Invalid stuck season order id: {stuck_order_id}')
        return 0
    return stuck_order_id


def get_target_stock_load_rate(stock, reserve, target_deadlines):
    effective_stock = max(stock - reserve, 0)
    rate_per_day = 0
    target_stock = 0
    for target_count, target_period in target_deadlines:
        deadline_rate = target_count / target_period
        if deadline_rate > rate_per_day + 1e-9:
            rate_per_day = deadline_rate
            target_stock = target_count
        elif abs(deadline_rate - rate_per_day) <= 1e-9:
            target_stock = max(target_stock, target_count)
    if effective_stock >= target_stock:
        return 0
    return rate_per_day


def is_integer_value(value):
    if isinstance(value, (int, np.integer)):
        return True
    if isinstance(value, (float, np.floating)):
        return float(value).is_integer()
    return False


def ceil_div_or_ceil(numerator, denominator):
    if is_integer_value(numerator) and is_integer_value(denominator):
        numerator = int(numerator)
        denominator = int(denominator)
        return (numerator + denominator - 1) // denominator
    return ceil_with_epsilon(numerator / denominator)


def ceil_with_epsilon(amount, epsilon=1e-9):
    from math import ceil
    return int(ceil(float(amount) - epsilon))


def format_item_need_data(data, format_amount):
    deadlines = data.get('deadlines')
    if not deadlines:
        return f'{format_amount(data["total_need_count"])} in {format_amount(data["period"])} day(s)'
    return ', '.join(
        f'{format_amount(deadline["count"])} in {format_amount(deadline["period"])} day(s)'
        for deadline in deadlines
    )


def item_need_data_to_yaml_entry(data, round_up_int):
    deadlines = data.get('deadlines')
    if deadlines and len(deadlines) > 1:
        previous_count = 0
        entries = []
        for deadline in deadlines:
            count = round_up_int(deadline['count'])
            period = round_up_int(deadline['period'])
            entries.append({
                'count': count - previous_count,
                'period': period,
            })
            previous_count = count
        return entries
    return {
        'count': round_up_int(data['total_need_count']),
        'period': round_up_int(data['period']),
    }


def get_sub_dict(raw_dict: Dict[int, bool], keys: list) -> Dict[int, bool]:
    return {key: raw_dict.get(key, False) for key in keys}


def count_level(substatus: Dict[int, bool]):
    return sum(1 for status in substatus.values() if status)
