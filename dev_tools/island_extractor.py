import re
from datetime import datetime
from pathlib import Path

from dev_tools.utils import LuaLoader


SERVERS = ('cn', 'en', 'jp', 'tw')
SEASON_ACTIVITY_TYPES = (5001, 5002, 5003, 5004)


def load_island_table(loader, name):
    """Index keyed and array-style Lua tables by their record IDs."""
    return {
        item.get('id', index): item
        for index, item in loader.load(f'sharecfg/{name}.lua').items()
        if isinstance(index, int)
    }


def localize_names(records, table, get_name=lambda item: item['name']):
    for server in SERVERS:
        loader = LuaLoader(LOADER.folder, server=server)
        for index, item in load_island_table(loader, table).items():
            if index in records:
                records[index]['name'][server] = get_name(item)


def encode_table(name, records, expand=False):
    """Preserve insertion order: ingredient mappings follow their UI positions."""
    lines = [f'{name} = {{']
    for key, value in records.items():
        if expand:
            lines.append(f'    {key!r}: {{')
            lines.extend(f'        {field!r}: {content!r},' for field, content in value.items())
            lines.append('    },')
        else:
            lines.append(f'    {key!r}: {value!r},')
    lines.append('}')
    return lines


def unpack_ingredient_dic(ingredients):
    return {entry[0]: entry[1] for entry in ingredients.values()}


def island_time_to_sql_time(island_time):
    """Convert the Lua {date, time} pair into a sortable timestamp."""
    date, time = island_time[0], island_time[1]
    return f'{date[0]:04}-{date[1]:02}-{date[2]:02} {time[0]:02}:{time[1]:02}:{time[2]:02}'


def dates_within_24_hours(first, second):
    try:
        first = datetime.strptime(first, '%Y-%m-%d %H:%M:%S')
        second = datetime.strptime(second, '%Y-%m-%d %H:%M:%S')
        return abs((first - second).total_seconds()) <= 86400
    except (ValueError, TypeError):
        return False


class IslandItemExtractor:
    def __init__(self):
        self.item = {
            0: {
                'name': {
                    'cn': '岛屿开发PT', 'en': 'Island Development Points',
                    'jp': '離島開発Pt', 'tw': '島嶼開發PT',
                },
                'pt_num': 1,
                'manage_influence': 0,
                'order_price': 0,
            },
        }
        self.item.update({
            index: {
                'name': dict.fromkeys(SERVERS, ''),
                'pt_num': item['pt_num'],
                'manage_influence': item['manage_influence'],
                'order_price': item['order_price'],
            }
            for index, item in load_island_table(LOADER, 'island_item_data_template').items()
            if not (1 < index < 1000 or index > 100000)
        })
        localize_names(self.item, 'island_item_data_template')


class IslandRecipeExtractor:
    def __init__(self):
        self.recipe = {
            index: self.extract_recipe(item)
            for index, item in load_island_table(LOADER, 'island_formula').items()
            if not 7000000 <= index < 9900000 and item['attribute'] in (1, 2, 3, 4, 6)
        }
        localize_names(self.recipe, 'island_formula')

    def extract_recipe(self, item):
        return {
            'name': dict.fromkeys(SERVERS, ''),
            'attribute': item['attribute'],
            'workload': item['workload'],  # Units of 0.1 seconds.
            'commission_cost': unpack_ingredient_dic(item['commission_cost']),
            'production_limit': item['production_limit'],
            'commission_product': unpack_ingredient_dic(item['commission_product']),
            'second_product_display': unpack_ingredient_dic(item['second_product_display']),
        }


class IslandProductionExtractor:
    def __init__(self):
        self.slot = {
            index: {
                'attribute': item['attribute'],
                'place': item['place'],
                'formula': list(item['formula'].values()),
            }
            for index, item in load_island_table(LOADER, 'island_production_slot').items()
            if 9000 <= index <= 10000
        }


def get_slot_ingredient_sources(slots, recipes, conversions, seasonal_formulas=None):
    """Find which slots can supply ingredients, including shop and fish exchanges."""
    seasonal_formulas = seasonal_formulas or {}
    products = {}
    ingredients = {}
    for slot_id, slot in slots.items():
        products[slot_id] = set()
        ingredients[slot_id] = set()
        for recipe_id in slot['formula'] + seasonal_formulas.get(slot_id, []):
            recipe = recipes[recipe_id]
            products[slot_id].update(recipe['commission_product'])
            products[slot_id].update(recipe['second_product_display'])
            ingredients[slot_id].update(recipe['commission_cost'])

        # These conversions can happen during dispatch without waiting for
        # another production slot: wheat -> flour, crops -> feed, fish -> meat.
        while True:
            converted = {
                item_id
                for conversion in conversions
                if products[slot_id].intersection(conversion['resource_consume'])
                for item_id in conversion['items']
            }
            if converted <= products[slot_id]:
                break
            products[slot_id].update(converted)

    return {
        slot_id: sorted(
            source_id for source_id, items in products.items()
            if items.intersection(cost)
        )
        for slot_id, cost in ingredients.items()
    }


class IslandActivityExtractor:
    def __init__(self):
        island_activities = load_island_table(LOADER, 'island_activity_template')
        activities = load_island_table(LOADER, 'activity_template')
        self.activity = {
            index: {
                'type': activities[index]['type'],
                'start_time': dict.fromkeys(SERVERS, ''),
                'end_time': dict.fromkeys(SERVERS, ''),
                'config_data': list(activities[index]['config_data'].values()),
            }
            for index in island_activities if index >= 990000
        }
        for server in SERVERS:
            loader = LuaLoader(LOADER.folder, server=server)
            for index, item in load_island_table(loader, 'activity_template').items():
                if index not in self.activity:
                    continue
                period = item['time']
                if period == 'always':
                    self.activity[index]['start_time'][server] = None
                    self.activity[index]['end_time'][server] = None
                elif isinstance(period, dict) and period[0] == 'timer':
                    self.activity[index]['start_time'][server] = island_time_to_sql_time(period[1])
                    self.activity[index]['end_time'][server] = island_time_to_sql_time(period[2])


class IslandWildGatherExtractor:
    # Lua only supplies the product icon. These observed yields are per gather
    # point, not the total across the two seasonal points of each product.
    item_id_to_count = {
        2606: 1,
        4001: 4,
        4002: 8,
        4003: 12,
        4004: 3,
        4015: 4,
        4016: 8,
        4017: 12,
        4018: 4,
        4029: 8,
        4030: 8,
        4031: 4,
        4032: 8,
        4043: 4,
        4044: 12,
        4045: 6,
        4046: 6,
    }

    def __init__(self):
        self.gather = {
            index: self.extract_gather(item)
            for index, item in load_island_table(LOADER, 'island_wild_gather').items()
        }

    def extract_gather(self, item):
        item_id = int(item['icon'].split('_')[-1])
        return {'product': {item_id: self.item_id_to_count[item_id]}}


class IslandSeasonExtractor:
    def __init__(self):
        self.season = {
            index: {
                'start_time': dict.fromkeys(SERVERS, ''),
                'end_time': dict.fromkeys(SERVERS, ''),
            }
            for index in load_island_table(LOADER, 'island_season')
        }
        for server in SERVERS:
            loader = LuaLoader(LOADER.folder, server=server)
            for index, item in load_island_table(loader, 'island_season').items():
                self.season[index]['start_time'][server] = island_time_to_sql_time(item['time'][0])
                self.season[index]['end_time'][server] = island_time_to_sql_time(item['time'][1])


class IslandTaskExtractor:
    def __init__(self):
        targets = load_island_table(LOADER, 'island_task_target')
        self.task = {
            index: self.extract_task(item, targets)
            for index, item in load_island_table(LOADER, 'island_task').items()
        }
        localize_names(self.task, 'island_task')

    def extract_task(self, item, targets):
        target_id = item['target_id'][0]
        target = targets.get(target_id, {})
        params = target.get('target_param')
        return {
            'name': dict.fromkeys(SERVERS, ''),
            'target_id': target_id,
            'target': {params[0]: target['target_num']} if isinstance(params, dict) else {},
        }


class IslandSeasonRequestExtractor:
    def __init__(self):
        self.request = {
            index: self.extract_order(item)
            for index, item in load_island_table(LOADER, 'island_order').items()
        }

    def extract_order(self, item):
        return {
            'activity_id': item['activity_id'],
            'group_id': item.get('group_id', item.get('groud_id', item['activity_id'])),
            'next_order': item['next_order'],
            'season_pt_num': item['season_pt_num'],
            'request': unpack_ingredient_dic(item['request']) if isinstance(item['request'], dict) else {},
            'award': {item['award'][0]: item['award'][1]} if isinstance(item['award'], dict) else {},
        }


class IslandShopExtractor:
    def __init__(self):
        self.shop = {}
        for index, item in load_island_table(LOADER, 'island_shop_template').items():
            if item['tag_type'] == 3:
                parent_id = item['second_shop']
            elif item['tag_type'] == 2:
                parent_id = item['first_shop']
            else:
                parent_id = None
            self.shop[index] = {
                'name': dict.fromkeys(SERVERS, ''),
                'tag_type': item['tag_type'],
                'order': item['order'],
                'parent_id': parent_id,
                'currency': [coin[2] for coin in item['top_resource'].values()]
                if isinstance(item['top_resource'], dict) else [],
                'goods': list(item['goods_id'].values()) if isinstance(item['goods_id'], dict) else [],
            }
        localize_names(self.shop, 'island_shop_template', lambda item: item['tag_icon'][0])

        # Correct the ordering of these shops in the Lua data.
        for index, order in ((10020, 1), (10021, 1), (10112, 2), (10113, 3)):
            self.shop[index]['order'] = order
        self.isolated_shop = {
            index: shop for index, shop in self.shop.items() if 10019 <= index < 10130
        }


class IslandShopItemExtractor:
    def __init__(self):
        self.item = {
            index: self.extract_goods(item)
            for index, item in load_island_table(LOADER, 'island_shop_goods').items()
            if 100000 <= index < 412000
        }
        self.item_to_recipe_id = {
            product: index for index, item in self.item.items() for product in item['items']
        }
        localize_names(self.item, 'island_shop_goods', lambda item: item['goods_name'])

    def extract_goods(self, item):
        return {
            'name': dict.fromkeys(SERVERS, ''),
            'resource_consume': {item['resource_consume'][1]: item['resource_consume'][2]},
            'items': {entry[1]: entry[2] for entry in item['items'].values()},
        }


class IslandExchangeRecipeExtractor:
    def __init__(self):
        self.item = {
            index: {
                'resource_consume': {item['origin_item']: 1},
                'items': {item['target_item']: item['target_num']},
            }
            for index, item in load_island_table(LOADER, 'island_exchange_template').items()
        }


class IslandProductionPlaceExtractor:
    def __init__(self):
        commissions = load_island_table(LOADER, 'island_production_commission')
        self.place = {
            index: {
                'name': dict.fromkeys(SERVERS, ''),
                'slot': [commissions[commission]['slot'] for commission in item['commission_slot'].values()],
            }
            for index, item in load_island_table(LOADER, 'island_production_place').items()
        }
        localize_names(self.place, 'island_production_place')
        for place in self.place.values():
            place['name']['cn'] = place['name']['cn'].strip()


class IslandRestaurantExtractor:
    def __init__(self):
        self.restaurant = {
            index: unpack_ingredient_dic(item['item_id'])
            for index, item in load_island_table(LOADER, 'island_manage_restaurant').items()
        }


class IslandTechnologyExtractor:
    def __init__(self):
        self.item = {
            index: {
                'name': dict.fromkeys(SERVERS, ''),
                'tech_belong': item['tech_belong'],
                'axis': (item['axis'][0], item['axis'][1]),
                'island_level': item['island_level'],
            }
            for index, item in load_island_table(LOADER, 'island_technology_template').items()
            if item['tech_belong'] != 1
        }
        localize_names(self.item, 'island_technology_template', lambda item: item['tech_name'])


def seasons_for_period(period, seasons, server='cn'):
    """Translate Lua timer ranges to season keys, ignoring maintenance hours.

    Seasons switch on their start date. Some activities start at midnight while
    the season switches at noon, so an overlap on that day alone must not
    activate the previous season. Ranges may cover more than one season.
    """
    if period == 'always':
        return list(seasons)
    if not isinstance(period, dict):
        return []
    start = island_time_to_sql_time(period[0])[:10]
    end = island_time_to_sql_time(period[1])[:10]
    return [
        key for key, season in seasons.items()
        if season['start_time'].get(server) and season['end_time'].get(server)
        and start < season['end_time'][server][:10]
        and season['start_time'][server][:10] < end
    ]


def changed_fields(server_data, current):
    """Return changed values, keeping localized names in the permanent catalog."""
    return {
        field: value for field, value in server_data.items()
        if field != 'name' and value != current.get(field)
    }


def read_season_namespaces():
    """Map CN release dates to the shared namespaces used by configuration."""
    namespaces = {}
    with open('module/island/README.md', encoding='utf-8') as f:
        for line in f:
            if re.match(r'^\|\s*\d{8}\s*\|', line):
                date, _, namespace, _, cn, _, _, _ = [cell.strip() for cell in line.strip('| \n').split('|')]
                if cn != '-':
                    namespaces[date] = namespace.replace(' ', '_')
    return namespaces


def get_season_namespace(start_time, end_time, seasons, server='cn'):
    """Match an observed server window to its canonical CN season namespace."""
    matches = [
        key for key, season in seasons.items()
        if dates_within_24_hours(start_time, season['start_time'].get(server))
        and dates_within_24_hours(end_time, season['end_time'].get(server))
    ]
    if len(matches) > 1:
        raise ValueError(f'Ambiguous {server} season window: {start_time} - {end_time}')
    return matches[0] if matches else None


class IslandSeasonDataExtractor:
    def __init__(self, recipes, production, shops, tasks, gathers, restaurants, exchanges):
        self.activity = IslandActivityExtractor().activity
        orders = IslandSeasonRequestExtractor()
        self.request = orders.request
        namespaces = read_season_namespaces()
        season_schedule = {}
        season_keys = {}
        self.season = {}
        for index, season in IslandSeasonExtractor().season.items():
            key = namespaces[season['start_time']['cn'][:10].replace('-', '')]
            season_schedule[key] = season
            season_keys[index] = key
            self.season[key] = {'id': index}
        self.server_overrides = {}
        self.seasonal_shop_goods = set()
        self.seasonal_tasks = set()
        sources = {}
        for server in SERVERS:
            loader = LuaLoader(LOADER.folder, server=server)
            source = {
                table: load_island_table(loader, table)
                for table in (
                    'island_season', 'activity_template', 'island_production_slot',
                    'island_wild_gather', 'island_shop_goods', 'island_formula',
                    'island_task', 'island_task_target', 'island_order',
                    'island_manage_restaurant',
                )
            }
            sources[server] = source
            self.seasonal_shop_goods.update(
                index for index, item in source['island_shop_goods'].items()
                if index in shops.item and item['time'] != 'always'
            )
            self.seasonal_tasks.update(
                index for index, item in source['island_task'].items()
                if item['unlock_time'] != 'always'
            )
            for item in source['island_season'].values():
                self.seasonal_tasks.update(item['task_list'].values())

            if server == 'cn':
                continue
            for index, item in source['island_manage_restaurant'].items():
                menu = restaurants.restaurant.setdefault(index, {})
                for entry in item['item_id'].values():
                    menu.setdefault(entry[0], entry[1])

            overrides = {}
            for field, table, baseline, encode in (
                ('recipe_overrides', 'island_formula', recipes.recipe, recipes.extract_recipe),
                ('shop_goods_overrides', 'island_shop_goods', shops.item, shops.extract_goods),
                ('task_overrides', 'island_task', tasks.task,
                 lambda item: tasks.extract_task(item, source['island_task_target'])),
                ('wild_gather_overrides', 'island_wild_gather', gathers.gather, gathers.extract_gather),
                ('season_order_overrides', 'island_order', self.request, orders.extract_order),
            ):
                changes = {
                    index: changed_fields(encode(item), baseline[index])
                    for index, item in source[table].items() if index in baseline
                }
                changes = {index: value for index, value in changes.items() if value}
                if changes:
                    overrides[field] = changes
            if overrides:
                self.server_overrides[server] = overrides

        # Slot tables retain only the current specialties. Item navigation still
        # identifies where the other retained recipes are produced.
        recipe_slots = self.get_recipe_slots(sources, production.slot)
        conversions = list(shops.item.values()) + list(exchanges.item.values())
        permanent_sources = get_slot_ingredient_sources(production.slot, recipes.recipe, conversions)
        for index, source_slots in permanent_sources.items():
            production.slot[index]['ingredient_source_slots'] = source_slots

        for server, source in sources.items():
            recipe_overrides = self.server_overrides.get(server, {}).get('recipe_overrides', {})
            effective_recipes = {
                index: {**recipe, **recipe_overrides.get(index, {})}
                for index, recipe in recipes.recipe.items()
            }
            activities = {season_keys[index]: {} for index in source['island_season']}
            for activity in source['activity_template'].values():
                period = activity['time']
                if activity['type'] not in SEASON_ACTIVITY_TYPES or not isinstance(period, dict):
                    continue
                if period.get(0) != 'timer':
                    continue
                key = get_season_namespace(
                    island_time_to_sql_time(period[1]), island_time_to_sql_time(period[2]), season_schedule, server,
                )
                if key not in activities:
                    continue
                if activity['type'] in activities[key]:
                    raise ValueError(f'{key}: multiple {server} activities of type {activity["type"]}')
                activities[key][activity['type']] = activity

            for index, server_season in source['island_season'].items():
                key = season_keys[index]
                season = self.season[key]
                by_type = activities[key]
                if set(by_type) != set(SEASON_ACTIVITY_TYPES):
                    raise ValueError(f'{key}: expected four {server} activities, got {list(by_type)}')
                slot_recipes = {}
                for recipe_id in sorted(by_type[5004]['config_data'].values()):
                    for slot_id in recipe_slots[recipe_id]:
                        slot_recipes.setdefault(slot_id, []).append(recipe_id)
                content = {
                    'task_list': list(server_season['task_list'].values()),
                    'activity': [by_type[kind]['id'] for kind in SEASON_ACTIVITY_TYPES],
                    'production': slot_recipes,
                    'wild_gather': {
                        index: gathers.extract_gather(source['island_wild_gather'][index])
                        for index in by_type[5003]['config_data'].values()
                    },
                    'shop_goods': sorted(
                        index for index, item in source['island_shop_goods'].items()
                        if index in self.seasonal_shop_goods
                        and key in seasons_for_period(item['time'], season_schedule, server)
                    ),
                }
                content['tasks'] = sorted(set(content['task_list']).union(
                    index for index, item in source['island_task'].items()
                    if item['unlock_time'] != 'always'
                    and key in seasons_for_period(item['unlock_time'], season_schedule, server)
                ))
                ingredient_sources = get_slot_ingredient_sources(
                    production.slot, effective_recipes, conversions, content['production'],
                )
                content['ingredient_source_slots'] = changed_fields(ingredient_sources, permanent_sources)
                if server == 'cn':
                    season.update(content)
                else:
                    differences = changed_fields(content, season)
                    if differences:
                        season.setdefault('server_overrides', {})[server] = differences

    def get_recipe_slots(self, sources, slots):
        recipe_slots = {}
        for source in sources.values():
            for index, item in source['island_production_slot'].items():
                if index not in slots:
                    continue
                for entry in item['activity_formula'].values():
                    for recipe_id in entry[1].values():
                        recipe_slots.setdefault(recipe_id, set()).add(index)

        source = sources['cn']
        items = load_island_table(LOADER, 'island_item_data_template')
        places = load_island_table(LOADER, 'island_production_place')
        commissions = load_island_table(LOADER, 'island_production_commission')
        recipe_ids = {
            recipe_id for activity in source['activity_template'].values()
            if activity['type'] == 5004 for recipe_id in activity['config_data'].values()
        }
        for recipe_id in sorted(recipe_ids - recipe_slots.keys()):
            product = items[source['island_formula'][recipe_id]['item_id']]
            matching_places = [
                place for place in places.values()
                if place['name'].strip() and any(
                    entry[0].strip().endswith(place['name'].strip()) for entry in product['jump_page'].values()
                )
            ]
            if len(matching_places) != 1:
                raise ValueError(f'Recipe {recipe_id}: expected one production place from item navigation')
            matched = {
                commissions[commission]['slot']
                for commission in matching_places[0]['commission_slot'].values()
            }.intersection(slots)
            if not matched:
                raise ValueError(f'Recipe {recipe_id}: item navigation has no production slots')
            recipe_slots[recipe_id] = matched
        return recipe_slots

    def encode(self):
        lines = []
        for name, data in (
            ('DIC_ISLAND_ACTIVITY', self.activity),
            ('DIC_ISLAND_SEASON_ORDER', self.request),
            ('DIC_ISLAND_SERVER_OVERRIDES', self.server_overrides),
            ('DIC_ISLAND_SEASON', self.season),
        ):
            lines.extend(encode_table(name, data, expand=name in ('DIC_ISLAND_SEASON', 'DIC_ISLAND_SERVER_OVERRIDES')))
            lines.append('')
        lines.append(f'DIC_ISLAND_SEASONAL_SHOP_GOODS = {sorted(self.seasonal_shop_goods)!r}')
        lines.append(f'DIC_ISLAND_SEASONAL_TASKS = {sorted(self.seasonal_tasks)!r}')
        return lines


def generate(folder='../AzurLaneLuaScripts', output='module/island'):
    global LOADER
    LOADER = LuaLoader(folder, server='CN')

    header = [
        '# This file was automatically generated by dev_tools/island_extractor.py',
        "# Don't modify it manually.",
        '',
    ]
    recipe_extractor = IslandRecipeExtractor()
    production_extractor = IslandProductionExtractor()
    shop_extractor = IslandShopItemExtractor()
    exchange_extractor = IslandExchangeRecipeExtractor()
    task_extractor = IslandTaskExtractor()
    gather_extractor = IslandWildGatherExtractor()
    restaurant_extractor = IslandRestaurantExtractor()
    season_extractor = IslandSeasonDataExtractor(
        recipe_extractor, production_extractor, shop_extractor, task_extractor,
        gather_extractor, restaurant_extractor, exchange_extractor,
    )
    lines = list(header)
    for name, data in (
        ('DIC_ISLAND_ITEM', IslandItemExtractor().item),
        ('DIC_ISLAND_RECIPE', recipe_extractor.recipe),
        ('DIC_ISLAND_SLOT', production_extractor.slot),
        ('DIC_ISLAND_WILD_GATHER', gather_extractor.gather),
        ('DIC_ISLAND_PRODUCTION_MINING', {index: {2700: 8} for index in range(40101, 40110)}),
        ('DIC_ISLAND_PRODUCTION_LOGGING', {index: {2800: 8} for index in range(40201, 40210)}),
        ('DIC_ISLAND_SHOP', IslandShopExtractor().isolated_shop),
        ('DIC_ISLAND_SHOP_RECIPE', shop_extractor.item),
        ('DIC_ISLAND_SHOP_ITEM_TO_RECIPE', shop_extractor.item_to_recipe_id),
        ('DIC_ISLAND_EXCHANGE_RECIPE', exchange_extractor.item),
        ('DIC_ISLAND_TASK', task_extractor.task),
        ('DIC_ISLAND_RESTAURANT_MENU_TO_RECIPE', restaurant_extractor.restaurant),
        ('DIC_ISLAND_TECHNOLOGY', IslandTechnologyExtractor().item),
        ('DIC_ISLAND_PRODUCTION_PLACE', IslandProductionPlaceExtractor().place),
    ):
        lines.extend(encode_table(name, data))
        lines.append('')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'data.py').write_text('\n'.join(lines), encoding='utf-8')
    (output / 'season_data.py').write_text('\n'.join(header + season_extractor.encode()) + '\n', encoding='utf-8')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate island data from the current CN, EN, JP and TW Lua directories.')
    parser.add_argument('--lua-folder', default='../AzurLaneLuaScripts')
    parser.add_argument('--output', default='module/island')
    args = parser.parse_args()
    generate(args.lua_folder, args.output)
