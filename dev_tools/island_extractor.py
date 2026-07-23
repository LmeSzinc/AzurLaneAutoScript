import re

from dev_tools.slpp import slpp
from dev_tools.utils import LuaLoader


class IslandItem:
    def __init__(self, item):
        """
        In the file 'sharecfg/island_item_data_template.lua':
        id: serial of this item
        name: name in server, default to CN
        pt_num: pt value of this item
        manage_influence: restaurant influence
        order_price: price in order system
        """
        self.id = item['id']
        # self.name = item['name']
        self.pt_num = item['pt_num']
        self.manage_influence = item['manage_influence']
        self.order_price = item['order_price']

    def encode(self):
        data = {
            # 'id': self.id,
            'name': {
                'cn': '',
                'en': '',
                'jp': '',
                # 'tw': '',
            },
            'pt_num': self.pt_num,
            'manage_influence': self.manage_influence,
            'order_price': self.order_price,
        }
        return data


class IslandItemExtractor:
    def __init__(self):
        self.item = {}

        data = LOADER.load('sharecfg/island_item_data_template.lua', keyword='pg.base.island_item_data_template')
        for index, item in data.items():
            if not isinstance(index, int) or 1 < index < 1000 or index > 100000:
                continue

            self.item[item['id']] = IslandItem(item).encode()

        for index, name in self.extract_item_name('zh-CN').items():
            self.item[index]['name']['cn'] = name
        for index, name in self.extract_item_name('en-US').items():
            self.item[index]['name']['en'] = name
        for index, name in self.extract_item_name('ja-JP').items():
            self.item[index]['name']['jp'] = name
        # for index, name in self.extract_item_name('zh-TW').items():
        #     self.item[index]['name']['tw'] = name

    def extract_item_name(self, server):
        LOADER.server = server
        data = LOADER.load('sharecfg/island_item_data_template.lua', keyword='pg.base.island_item_data_template')
        out = {}
        for index, item in data.items():
            if not isinstance(index, int) or 1 < index < 1000 or index > 100000:
                continue
            out[item['id']] = item['name']

        return out

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_ITEM = {')
        lines.append("    0: {'name': {'cn': '岛屿开发PT', 'en': 'Island Development Points', 'jp': '離島開発Pt'}, 'pt_num': 1, 'manage_influence': 0, 'order_price': 0},")
        for index, item in self.item.items():
            lines.append(f'    {index}: {item},')
        lines.append('}')
        return lines

    def write(self, file):
        print(f'writing {file}')
        with open(file, 'w', encoding='utf-8') as f:
            for text in self.encode():
                f.write(text + '\n')


def unpack_ingredient_dic(dic):
    try:
        result = {}
        for _, entry in dic.items():
            # print(entry)
            result[entry[0]] = entry[1]
        return result
    except TypeError:
        print(dic)
        raise


class IslandRecipe:
    def __init__(self, recipe):
        """
        In the file 'sharecfg/island_formula.lua':
        id: serial of this recipe
        name: name in server, default to CN
        workload: using time with unit 0.1 second.
        commission_cost: a nested dict of ingredients, each being a pair of item id and count
        production_limit: consecutive commission upper bound for one commission handle
        commission_product: a nested dict of products, each (only one) being a pair of item id and count
        second_product_display: a nested dict of products, each being a pair of item id and count.
        """
        self.id = recipe['id']
        # self.name = recipe['name']
        self.workload = recipe['workload']
        self.commission_cost = recipe['commission_cost']
        self.production_limit = recipe['production_limit']
        self.commission_product = recipe['commission_product']
        self.second_product_display = recipe['second_product_display']

    def encode(self):
        data = {
            self.id: {
                'name': {
                    'cn': '',
                    'en': '',
                    'jp': '',
                    # 'tw': '',
                },
                'workload': self.workload,
                'commission_cost': unpack_ingredient_dic(self.commission_cost),
                'production_limit': self.production_limit,
                'commission_product': unpack_ingredient_dic(self.commission_product),
                'second_product_display': unpack_ingredient_dic(self.second_product_display),
            }
        }
        return data


class IslandRecipeExtractor:
    def __init__(self):
        self.recipe = {}
        data = LOADER.load('sharecfg/island_formula.lua')
        for index, item in data.items():
            if not isinstance(index, int) or not (index // 10000 < 700 or index // 10000 >= 990):
                continue
            if item['attribute'] in [1, 2, 3, 4, 6]:
                self.recipe.update(IslandRecipe(item).encode())

                # print(item['id'],
                #       item['name'],
                #       item['workload'] // 10,
                #       item['commission_cost'],
                #       item['production_limit'],
                #       item['commission_product'],
                #       item['second_product_display'])
        for index, name in self.extract_item_name('zh-CN').items():
            if index in self.recipe:
                self.recipe[index]['name']['cn'] = name
        for index, name in self.extract_item_name('en-US').items():
            if index in self.recipe:
                self.recipe[index]['name']['en'] = name
        for index, name in self.extract_item_name('ja-JP').items():
            if index in self.recipe:
                self.recipe[index]['name']['jp'] = name
        # for index, name in self.extract_item_name('zh-TW').items():
        #     if index in self.recipe:
        #         self.recipe[index]['name']['tw'] = name

    def extract_item_name(self, server):
        LOADER.server = server
        data = LOADER.load('sharecfg/island_formula.lua')
        out = {}
        for index, item in data.items():
            if not isinstance(index, int) or not (index // 10000 < 700 or index // 10000 >= 990):
                continue
            if item['attribute'] in [1, 2, 3, 4, 6]:
                out[item['id']] = item['name']

        return out

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_RECIPE = {')
        for index, recipe in self.recipe.items():
            lines.append(f'    {index}: {recipe},')
        lines.append('}')
        return lines

    def write(self, file):
        print(f'writing {file}')
        with open(file, '', encoding='utf-8') as f:
            for text in self.encode():
                f.write(text + '\n')


def unpack_activity_formula(dic):
    try:
        result = []
        for _, entry in dic.items():
            result += [item for _, item in entry[1].items()]
        return result
    except TypeError:
        print(dic)


class IslandProduction:
    def __init__(self, slot):
        """
        In the file 'sharecfg/island_production_slot.lua':
        attribute: 1 = agriculture, 2 = mineral, 3 = animal, 4 = restaurant, 6 = industry
        place: slot position
        exclusion_slot: id of slots that are exclusive to this slot, not necessary for our implementation
        formula: applicable recipes
        activity_formula: activity id and activity recipes
        """
        self.id = slot['id']
        self.attribute = slot['attribute']
        self.place = slot['place']
        self.formula = [item for _, item in slot['formula'].items()]
        self.activity_formula = unpack_activity_formula(slot['activity_formula'])

    def encode(self):
        data = {
            self.id: {
                'attribute': self.attribute,
                'place': self.place,
                'formula': self.formula,
                'activity_formula': self.activity_formula,
            }
        }
        return data


class IslandProductionExtractor:
    def __init__(self):
        self.slot = {}
        data = LOADER.load('sharecfg/island_production_slot.lua')
        for index, item in data.items():
            if not isinstance(index, int) or index < 9000 or index > 10000:
                continue
            # print(item['attribute'], item['place'], item['formula'], item['activity_formula'])
            self.slot.update(IslandProduction(item).encode())

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_SLOT = {')
        for index, slot in self.slot.items():
            lines.append(f'    {index}: {slot},')
        lines.append('}')
        return lines

    def write(self, file):
        print(f'writing {file}')
        with open(file, 'w', encoding='utf-8') as f:
            for text in self.encode():
                f.write(text + '\n')


def island_time_to_sql_time(island_time):
    """
    island_time is like {0: {0: 2026, 1: 2, 2: 5}, 1: {0: 12, 1: 0, 2: 0}}
    """
    year = island_time[0][0]
    month = island_time[0][1]
    day = island_time[0][2]
    hour = island_time[1][0]
    minute = island_time[1][1]
    second = island_time[1][2]
    return f'{year:04}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}'


class Activity:
    def __init__(self, activity):
        """
        In the file 'sharecfg/activity_template.lua':
        id: serial of this activity
        type:
            5001: Specialties, Pearl Trade
            5002: Order
            5003: Wild Gather
            5004: Recipe
            800:
        config_data: config data of this activity
        """
        self.id = activity['id']
        self.type = activity['type']
        self.config_data = [config for _, config in activity['config_data'].items()]

    def encode(self):
        data = {
            'type': self.type,
            'start_time': {
                'cn': '',
                'en': '',
                'jp': '',
                # 'tw': '',
            },
            'end_time': {
                'cn': '',
                'en': '',
                'jp': '',
                # 'tw': '',
            },
            'config_data': self.config_data,
        }
        return data


class IslandActivityExtractor:
    def __init__(self):
        self.activity = {}
        data = LOADER.load('sharecfg/island_activity_template.lua')
        for index, item in data.items():
            if not isinstance(index, int) or index < 990000:
                continue
            self.activity[index] = None
        data = LOADER.load('sharecfg/activity_template.lua')
        for index, item in data.items():
            if not isinstance(index, int) or not index in self.activity:
                continue
            self.activity[index] = Activity(item).encode()
        for index, item in self.extract_item_name('zh-CN').items():
            if item['time'] == 'always':
                self.activity[index]['start_time']['cn'] = None
                self.activity[index]['end_time']['cn'] = None
            elif isinstance(item['time'], dict) and item['time'][0] == 'timer':
                try:
                    self.activity[index]['start_time']['cn'] = island_time_to_sql_time(item['time'][1])
                    self.activity[index]['end_time']['cn'] = island_time_to_sql_time(item['time'][2])
                except KeyError as e:
                    print(self.activity[index])
                    raise e
        for index, item in self.extract_item_name('en-US').items():
            if item['time'] == 'always':
                self.activity[index]['start_time']['en'] = None
                self.activity[index]['end_time']['en'] = None
            elif isinstance(item['time'], dict) and item['time'][0] == 'timer':
                self.activity[index]['start_time']['en'] = island_time_to_sql_time(item['time'][1])
                self.activity[index]['end_time']['en'] = island_time_to_sql_time(item['time'][2])
        for index, item in self.extract_item_name('ja-JP').items():
            if item['time'] == 'always':
                self.activity[index]['start_time']['jp'] = None
                self.activity[index]['end_time']['jp'] = None
            elif isinstance(item['time'], dict) and item['time'][0] == 'timer':
                self.activity[index]['start_time']['jp'] = island_time_to_sql_time(item['time'][1])
                self.activity[index]['end_time']['jp'] = island_time_to_sql_time(item['time'][2])
        # for index, item in self.extract_item_name('zh-TW').items():
        #     if item['time'] == 'always':
        #         self.activity[index]['start_time']['tw'] = None
        #         self.activity[index]['end_time']['tw'] = None
        #     elif isinstance(item['time'], dict) and item['time'][0] == 'timer':
        #         self.activity[index]['start_time']['tw'] = island_time_to_sql_time(item['time'][1])
        #         self.activity[index]['end_time']['tw'] = island_time_to_sql_time(item['time'][2])

    def extract_item_name(self, server):
        LOADER.server = server
        data = LOADER.load('sharecfg/activity_template.lua')
        out = {}
        for index, item in data.items():
            if not isinstance(index, int) or not index in self.activity:
                continue
            out[item['id']] = item
        return out
    
    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_ACTIVITY = {')
        for index, activity in self.activity.items():
            lines.append(f'    {index}: {activity},')
        lines.append('}')
        return lines
    
    def write(self, file):
        print(f'writing {file}')
        with open(file, 'w', encoding='utf-8') as f:
            for text in self.encode():
                f.write(text + '\n')


class IslandWildGatherExtractor:
    def __init__(self):
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
        }
        self.gather = {}
        data = LOADER.load('sharecfg/island_wild_gather.lua')
        for index, item in data.items():
            if not isinstance(index, int):
                continue
            item_id = int(item['icon'].split('_')[-1])
            self.gather[index] = {
                'activity_id': item['activity_id'],
                'product': {item_id: item_id_to_count[item_id]},
            }

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_WILD_GATHER = {')
        for index, gather in self.gather.items():
            lines.append(f'    {index}: {gather},')
        lines.append('}')
        return lines
        


class IslandProductionMiningExtractor:
    def __init__(self):
        self.mining = {}
        for index in range(40101, 40110):
            self.mining[index] = {2700: 8}
    
    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_PRODUCTION_MINING = {')
        for index, mining in self.mining.items():
            lines.append(f'    {index}: {mining},')
        lines.append('}')
        return lines


class IslandProductionLoggingExtractor:
    def __init__(self):
        self.logging = {}
        for index in range(40201, 40210):
            self.logging[index] = {2800: 8}
    
    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_PRODUCTION_LOGGING = {')
        for index, logging in self.logging.items():
            lines.append(f'    {index}: {logging},')
        lines.append('}')
        return lines


class IslandSeasonExtractor:
    def __init__(self, activity_dict=None):
        self.season = {}
        data = LOADER.load('sharecfg/island_season.lua')
        for index, item in data.items():
            if not isinstance(index, int):
                continue
            self.season[item['id']] = {
                'start_time': {
                    'cn': '',
                    'en': '',
                    'jp': '',
                    # 'tw': '',
                },
                'end_time': {
                    'cn': '',
                    'en': '',
                    'jp': '',
                    # 'tw': '',
                },
                'task_list': [task for _, task in item['task_list'].items()],
            }
        for index, item in self.extract_item_name('zh-CN').items():
            self.season[index]['start_time']['cn'] = island_time_to_sql_time(item['time'][0])
            self.season[index]['end_time']['cn'] = island_time_to_sql_time(item['time'][1])
        for index, item in self.extract_item_name('en-US').items():
            self.season[index]['start_time']['en'] = island_time_to_sql_time(item['time'][0])
            self.season[index]['end_time']['en'] = island_time_to_sql_time(item['time'][1])
        for index, item in self.extract_item_name('ja-JP').items():
            self.season[index]['start_time']['jp'] = island_time_to_sql_time(item['time'][0])
            self.season[index]['end_time']['jp'] = island_time_to_sql_time(item['time'][1])
        # for index, item in self.extract_item_name('zh-TW').items():
        #     self.season[index]['start_time']['tw'] = island_time_to_sql_time(item['time'][0])
        #     self.season[index]['end_time']['tw'] = island_time_to_sql_time(item['time'][1])
        if activity_dict is None:
            print('activity_dict is None, skipping season-activity matching')
            return
        for index, season in self.season.items():
            for activity_id, activity in activity_dict.items():
                if season['start_time']['cn'] is not None and season['end_time']['cn'] is not None and activity['start_time']['cn'] is not None and activity['end_time']['cn'] is not None:
                    if season['start_time']['cn'] == activity['start_time']['cn'] and season['end_time']['cn'] == activity['end_time']['cn']:
                        season.setdefault('activity', []).append(activity_id)

    def extract_item_name(self, server):
        LOADER.server = server
        data = LOADER.load('sharecfg/island_season.lua')
        out = {}
        for index, item in data.items():
            if not isinstance(index, int):
                continue
            out[item['id']] = item
        return out

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_SEASON = {')
        for index, season in self.season.items():
            lines.append(f'    {index}: {season},')
        lines.append('}')
        return lines
    

class IslandTaskExtractor:
    def __init__(self):
        self.task = {}
        target_id_to_task_id = {}
        data = LOADER.load('sharecfg/island_task.lua')
        for index, item in data.items():
            if not isinstance(index, int):
                continue
            self.task[item['id']] = {
                'name': {
                    'cn': '',
                    'en': '',
                    'jp': '',
                    # 'tw': '',
                },
                'target_id': item['target_id'][0],
                'target': {},
                'start_time': {
                    'cn': None,
                    'en': None,
                    'jp': None,
                    # 'tw': None,
                },
                'end_time': {
                    'cn': None,
                    'en': None,
                    'jp': None,
                    # 'tw': None,
                },
            }
            target_id_to_task_id[item['target_id'][0]] = item['id']
        for index, item in self.extract_item('zh-CN').items():
            self.task[index]['name']['cn'] = item['name']
            time_dict = item['unlock_time']
            if time_dict == 'stop':
                self.task[index]['start_time']['cn'] = None
                self.task[index]['end_time']['cn'] = None
            elif time_dict == 'always':
                self.task[index]['start_time']['cn'] = 'always'
                self.task[index]['end_time']['cn'] = 'always'
            else:
                self.task[index]['start_time']['cn'] = island_time_to_sql_time(time_dict[0])
                self.task[index]['end_time']['cn'] = island_time_to_sql_time(time_dict[1])
        for index, item in self.extract_item('en-US').items():
            self.task[index]['name']['en'] = item['name']
            time_dict = item['unlock_time']
            if time_dict == 'stop':
                self.task[index]['start_time']['en'] = None
                self.task[index]['end_time']['en'] = None
            elif time_dict == 'always':
                self.task[index]['start_time']['en'] = 'always'
                self.task[index]['end_time']['en'] = 'always'
            else:
                self.task[index]['start_time']['en'] = island_time_to_sql_time(time_dict[0])
                self.task[index]['end_time']['en'] = island_time_to_sql_time(time_dict[1])
        for index, item in self.extract_item('ja-JP').items():
            self.task[index]['name']['jp'] = item['name']
            time_dict = item['unlock_time']
            if time_dict == 'stop':
                self.task[index]['start_time']['jp'] = None
                self.task[index]['end_time']['jp'] = None
            elif time_dict == 'always':
                self.task[index]['start_time']['jp'] = 'always'
                self.task[index]['end_time']['jp'] = 'always'
            else:
                self.task[index]['start_time']['jp'] = island_time_to_sql_time(time_dict[0])
                self.task[index]['end_time']['jp'] = island_time_to_sql_time(time_dict[1])
        # for index, item in self.extract_item('zh-TW').items():
        #     self.task[index]['name']['tw'] = item['name']
        #     time_dict = item['unlock_time']
        #     if time_dict == 'stop':
        #         self.task[index]['start_time']['tw'] = None
        #         self.task[index]['end_time']['tw'] = None
        #     elif time_dict == 'always':
        #         self.task[index]['start_time']['tw'] = 'always'
        #         self.task[index]['end_time']['tw'] = 'always'
        #     else:
        #         self.task[index]['start_time']['tw'] = island_time_to_sql_time(time_dict[0])
        #         self.task[index]['end_time']['tw'] = island_time_to_sql_time(time_dict[1])
        
        data = LOADER.load('sharecfg/island_task_target.lua')
        for index, item in data.items():
            if not isinstance(index, int) or not item['id'] in target_id_to_task_id:
                continue
            task_id = target_id_to_task_id[item['id']]
            if isinstance(item['target_param'], dict):
                self.task[task_id]['target'] = {item['target_param'][0]: item['target_num']}

    def extract_item(self, server):
        LOADER.server = server
        data = LOADER.load('sharecfg/island_task.lua')
        out = {}
        for index, item in data.items():
            if not isinstance(index, int) or not item['id'] in self.task.keys():
                continue
            out[item['id']] = item

        return out
    
    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_TASK = {')
        for index, task in self.task.items():
            lines.append(f'    {index}: {task},')
        lines.append('}')
        return lines


class IslandSeasonRequest:
    def __init__(self, item):
        self.activity_id = item['activity_id']
        self.next_order = item['next_order']
        self.season_pt_num = item['season_pt_num']
        self.request = {request[0]: request[1] for _, request in item['request'].items()} if isinstance(item['request'], dict) else {}
        self.award = {item['award'][0]: item['award'][1]} if isinstance(item['award'], dict) else {}

    def encode(self):
        data = {
            'activity_id': self.activity_id,
            'next_order': self.next_order,
            'season_pt_num': self.season_pt_num,
            'request': self.request,
            'award': self.award,
        }
        return data
    

class IslandSeasonRequestExtractor:
    def __init__(self):
        self.request = {}
        data = LOADER.load('sharecfg/island_order.lua')
        for index, item in data.items():
            if not isinstance(index, int):
                continue
            self.request[index] = IslandSeasonRequest(item).encode()

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_SEASON_ORDER = {')
        for index, request in self.request.items():
            lines.append(f'    {index}: {request},')
        lines.append('}')
        return lines


class IslandShop:
    # item with top resource will be recorded
    def __init__(self, item):
        self.tag_type = item['tag_type']
        self.order = item['order']
        if self.tag_type == 3:
            self.parent_id = item['second_shop']
        elif self.tag_type == 2:
            self.parent_id = item['first_shop']
        else:
            self.parent_id = None
        self.currency = [coin[2] for _, coin in item['top_resource'].items()] if isinstance(item['top_resource'], dict) else []
        self.goods = [shop_recipe_id for _, shop_recipe_id in item['goods_id'].items()] if isinstance(item['goods_id'], dict) else []

    def encode(self):
        data = {
            'name': {
                'cn': '',
                'en': '',
                'jp': '',
                # 'tw': '',
            },
            'tag_type': self.tag_type,
            'order': self.order,
            'parent_id': self.parent_id,
            'currency': self.currency,
            'goods': self.goods,
        }
        return data


class IslandShopExtractor:
    def __init__(self):
        self.shop = {}
        data = LOADER.load('sharecfg/island_shop_template.lua')
        for index, item in data.items():
            self.shop[index] = IslandShop(item).encode()
        for index, item in self.extract_item('zh-CN').items():
            self.shop[index]['name']['cn'] = item['tag_icon'][0]
        for index, item in self.extract_item('en-US').items():
            self.shop[index]['name']['en'] = item['tag_icon'][0]
        for index, item in self.extract_item('ja-JP').items():
            self.shop[index]['name']['jp'] = item['tag_icon'][0]
        # for index, item in self.extract_item('zh-TW').items():
        #     self.shop[index]['name']['tw'] = item['tag_icon'][0]

        # Fix bug of lua data to make sure the order of shops is correct
        self.shop[10020]['order'] = 1
        self.shop[10021]['order'] = 1
        self.shop[10112]['order'] = 2
        self.shop[10113]['order'] = 3
        self.isolated_shop = {index: shop for index, shop in self.shop.items() if 10019 <= index < 10130}

    def extract_item(self, server):
        LOADER.server = server
        data = LOADER.load('sharecfg/island_shop_template.lua')
        out = {}
        for index, item in data.items():
            out[index] = item

        return out

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_SHOP = {')
        for index, shop in sorted(self.isolated_shop.items()):
            lines.append(f'    {index}: {shop},')
        lines.append('}')
        return lines


class IslandShopItemExtractor:
    def __init__(self):
        self.item = {}
        self.item_to_recipe_id = {}
        data = LOADER.load('sharecfg/island_shop_goods.lua', keyword='pg.base.island_shop_goods')
        for index, item in data.items():
            if not isinstance(index, int) or index < 100000 or index >= 412000:
                continue
            self.item[index] = {
                'name': {
                    'cn': '',
                    'en': '',
                    'jp': '',
                    # 'tw': '',
                },
                'resource_consume': {item['resource_consume'][1]: item['resource_consume'][2]},
                'items': {
                    itm[1]: itm[2] for _, itm in item['items'].items()
                },
                'start_time': {
                    'cn': None,
                    'en': None,
                    'jp': None,
                    # 'tw': None,
                },
                'end_time': {
                    'cn': None,
                    'en': None,
                    'jp': None,
                    # 'tw': None,
                }
            }
            for _, itm in item['items'].items():
                self.item_to_recipe_id[itm[1]] = index
        
        for index, item in self.extract_item('zh-CN').items():
            self.item[index]['name']['cn'] = item['goods_name']
            time_dict = item['time']
            if time_dict == 'always':
                self.item[index]['start_time']['cn'] = 'always'
                self.item[index]['end_time']['cn'] = 'always'
            else:
                self.item[index]['start_time']['cn'] = island_time_to_sql_time(time_dict[0])
                self.item[index]['end_time']['cn'] = island_time_to_sql_time(time_dict[1])
        for index, item in self.extract_item('en-US').items():
            self.item[index]['name']['en'] = item['goods_name']
            time_dict = item['time']
            if time_dict == 'always':
                self.item[index]['start_time']['en'] = 'always'
                self.item[index]['end_time']['en'] = 'always'
            else:
                self.item[index]['start_time']['en'] = island_time_to_sql_time(time_dict[0])
                self.item[index]['end_time']['en'] = island_time_to_sql_time(time_dict[1])
        for index, item in self.extract_item('ja-JP').items():
            self.item[index]['name']['jp'] = item['goods_name']
            time_dict = item['time']
            if time_dict == 'always':
                self.item[index]['start_time']['jp'] = 'always'
                self.item[index]['end_time']['jp'] = 'always'
            else:
                self.item[index]['start_time']['jp'] = island_time_to_sql_time(time_dict[0])
                self.item[index]['end_time']['jp'] = island_time_to_sql_time(time_dict[1])
        # for index, item in self.extract_item('zh-TW').items():
        #     self.item[index]['name']['tw'] = item['goods_name']
        #     time_dict = item['time']
        #     if time_dict == 'always':
        #         self.item[index]['start_time']['tw'] = 'always'
        #         self.item[index]['end_time']['tw'] = 'always'
        #     else:
        #         self.item[index]['start_time']['tw'] = island_time_to_sql_time(time_dict[0])
        #         self.item[index]['end_time']['tw'] = island_time_to

    def extract_item(self, server):
        LOADER.server = server
        data = LOADER.load('sharecfg/island_shop_goods.lua', keyword='pg.base.island_shop_goods')
        out = {}
        for index, item in data.items():
            if not isinstance(index, int) or index < 100000 or index >= 412000:
                continue
            out[index] = item

        return out

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_SHOP_RECIPE = {')
        for index, item in self.item.items():
            lines.append(f'    {index}: {item},')
        lines.append('}')
        lines.append('')
        lines.append('DIC_ISLAND_SHOP_ITEM_TO_RECIPE = {')
        for item_id, recipe_id in self.item_to_recipe_id.items():
            lines.append(f'    {item_id}: {recipe_id},')
        lines.append('}')
        return lines



class IslandExchangeRecipeExtractor:
    def __init__(self):
        self.item = {}
        data = LOADER.load('sharecfg/island_exchange_template.lua')
        for index, item in data.items():
            if not isinstance(index, int):
                continue
            self.item[index] = {
                'resource_consume': {item['origin_item']: 1},
                'items': {
                    item['target_item']: item['target_num']
                },
            }

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_EXCHANGE_RECIPE = {')
        for index, item in self.item.items():
            lines.append(f'    {index}: {item},')
        lines.append('}')
        return lines


class IslandProductionCommission:
    def __init__(self):
        self.commission = {}
        data = LOADER.load('sharecfg/island_production_commission.lua')
        for index, item in data.items():
            if not isinstance(index, int):
                continue
            self.commission[index] = item['slot']



class IslandProductionPlaceExtractor(IslandProductionCommission):
    def __init__(self):
        super().__init__()
        self.place = {}
        data = LOADER.load('sharecfg/island_production_place.lua')
        for index, item in data.items():
            if not isinstance(index, int):
                continue
            self.place[index] = {
                'name': {
                    'cn': '',
                    'en': '',
                    'jp': '',
                    # 'tw': '',
                },
                'slot': [self.commission[slot_id] for slot_id in item['commission_slot'].values()]
            }
        for index, name in self.extract_place_name('zh-CN').items():
            self.place[index]['name']['cn'] = name.strip()
        for index, name in self.extract_place_name('en-US').items():
            self.place[index]['name']['en'] = name
        for index, name in self.extract_place_name('ja-JP').items():
            self.place[index]['name']['jp'] = name
        # for index, name in self.extract_place_name('zh-TW').items():
        #     self.item[index]['name']['tw'] = name

    def extract_place_name(self, server):
        LOADER.server = server
        data = LOADER.load('sharecfg/island_production_place.lua')
        out = {}
        for index, item in data.items():
            if not isinstance(index, int):
                continue
            out[item['id']] = item['name']

        return out

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_PRODUCTION_PLACE = {')
        for index, place in self.place.items():
            lines.append(f'    {index}: {place},')
        lines.append('}')
        return lines

    def write(self, file):
        print(f'writing {file}')
        with open(file, 'w', encoding='utf-8') as f:
            for text in self.encode():
                f.write(text + '\n')


class IslandRestaurantExtractor:
    def __init__(self):
        self.restaurant = {}
        data = LOADER.load('sharecfg/island_manage_restaurant.lua')
        for index, item in data.items():
            if not isinstance(index, int):
                continue
            self.restaurant.update({
                item['id']: {
                    recipe[0]: recipe[1] for _, recipe in item['item_id'].items()
                }
            })

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_RESTAURANT_MENU_TO_RECIPE = {')
        for index, restaurant in self.restaurant.items():
            lines.append(f'    {index}: {restaurant},')
        lines.append('}')
        return lines

    def write(self, file):
        print(f'writing {file}')
        with open(file, 'w', encoding='utf-8') as f:
            for text in self.encode():
                f.write(text + '\n')


class IslandTechnology:
    def __init__(self, item):
        self.id = item['id']
        self.tech_belong = item['tech_belong']
        self.axis_x = item['axis'][0]
        self.axis_y = item['axis'][1]
        self.island_level = item['island_level']

    def encode(self):
        data = {
            'name': {
                'cn': '',
                'en': '',
                'jp': '',
                # 'tw': '',
            },
            'tech_belong': self.tech_belong,
            'axis': (self.axis_x, self.axis_y),
            'island_level': self.island_level,
        }
        return data

class IslandTechnologyExtractor:
    def __init__(self):
        self.item = {}

        data = LOADER.load('sharecfg/island_technology_template.lua', keyword='pg.base.island_technology_template')
        for index, item in data.items():
            if not isinstance(index, int) or item['tech_belong'] == 1:
                continue

            self.item[item['id']] = IslandTechnology(item).encode()

        for index, name in self.extract_item_name('zh-CN').items():
            self.item[index]['name']['cn'] = name
        for index, name in self.extract_item_name('en-US').items():
            self.item[index]['name']['en'] = name
        for index, name in self.extract_item_name('ja-JP').items():
            self.item[index]['name']['jp'] = name
        # for index, name in self.extract_item_name('zh-TW').items():
        #     self.item[index]['name']['tw'] = name

        # sort by id
        self.item = dict(sorted(self.item.items(), key=lambda x: x[0]))

    def extract_item_name(self, server):
        LOADER.server = server
        data = LOADER.load('sharecfg/island_technology_template.lua', keyword='pg.base.island_technology_template')
        out = {}
        for index, item in data.items():
            if not isinstance(index, int) or item['tech_belong'] == 1:
                continue
            out[item['id']] = item['tech_name']

        return out

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_TECHNOLOGY = {')
        for index, item in self.item.items():
            lines.append(f'    {index}: {item},')
        lines.append('}')
        return lines

    def write(self, file):
        print(f'writing {file}')
        with open(file, 'w', encoding='utf-8') as f:
            for text in self.encode():
                f.write(text + '\n')


if __name__ == '__main__':
    FILE = '../AzurLaneLuaScripts'
    LOADER = LuaLoader(FILE, server='CN')
    save = './module/island/data.py'

    lines = []
    lines.append('# This file was automatically generated by dev_tools/island_extractor.py')
    lines.append("# Don't modify it manually.")
    lines.append('')

    lines += IslandItemExtractor().encode()
    lines.append('')
    lines += IslandRecipeExtractor().encode()
    lines.append('')
    lines += IslandProductionExtractor().encode()
    lines.append('')
    activity_extractor = IslandActivityExtractor()
    lines += activity_extractor.encode()
    lines.append('')
    lines += IslandWildGatherExtractor().encode()
    lines.append('')
    lines += IslandProductionMiningExtractor().encode()
    lines.append('')
    lines += IslandProductionLoggingExtractor().encode()
    lines.append('')
    lines += IslandSeasonExtractor(activity_extractor.activity).encode()
    lines.append('')
    lines += IslandSeasonRequestExtractor().encode()
    lines.append('')
    lines += IslandShopExtractor().encode()
    lines.append('')
    lines += IslandShopItemExtractor().encode()
    lines.append('')
    lines += IslandExchangeRecipeExtractor().encode()
    lines.append('')
    lines += IslandTaskExtractor().encode()
    lines.append('')
    lines += IslandRestaurantExtractor().encode()
    lines.append('')
    lines += IslandTechnologyExtractor().encode()
    lines.append('')
    lines += IslandProductionPlaceExtractor().encode()
    with open(save, 'w', encoding='utf-8') as f:
        for text in lines:
            f.write(text + '\n')
