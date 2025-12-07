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
            if not isinstance(index, int) or 0 < index < 1000 or index > 100000:
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
            if not isinstance(index, int) or 0 < index < 1000 or index > 100000:
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
        # self.production_limit = recipe['production_limit']
        self.commission_product = recipe['commission_product']
        self.second_product_display = recipe['second_product_display']

    def encode(self):
        data = {
            self.id: {
                # 'name': self.name,
                'workload': self.workload,
                'commission_cost': unpack_ingredient_dic(self.commission_cost),
                # 'production_limit': self.production_limit,
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
        type: 1 = agriculture, 2 = mineral, 3 = animal, 4 = restaurant, 6 = industry
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


class IslandShopItemExtractor:
    def __init__(self):
        self.item = {}
        data = LOADER.load('sharecfg/island_shop_goods.lua', keyword='pg.base.island_shop_goods')
        for index, item in data.items():
            if not isinstance(index, int) or index < 100000 or index >= 412000:
                continue
            try:
                self.item[index] = {
                    'resource_consume': {item['resource_consume'][1]: item['resource_consume'][2]},
                    'items': {
                        itm[1]: itm[2] for _, itm in item['items'].items()
                    },
                }
                # print(self.item[index])
            except Exception:
                print(index, item)
                raise

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_SHOP_ITEM = {')
        for index, item in self.item.items():
            lines.append(f'    {index}: {item},')
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


class IslandSeason:
    def __init__(self, season):
        """
        In the file 'sharecfg/island_season.lua':
        id: serial of this season
        time: time range of this season
        task_list: list of tasks in this season
        """
        # self.id = season['id']
        self.end_time = island_time_to_sql_time(season['time'][1])
        self.task_list = [task + 10000 - 100 if task in range(80001100, 80001131) else task for _, task in season['task_list'].items()]

    def encode(self):
        data = {
            'end_time': self.end_time,
            'task_list': self.task_list,
        }
        return data

class IslandSeasonExtractor:
    def __init__(self):
        self.season = {}
        data = LOADER.load('sharecfg/island_season.lua')
        for index, item in data.items():
            if not isinstance(index, int):
                continue
            # print(item['task_list'].values())
            self.season[item['id']] = IslandSeason(item).encode()
        # print(self.season)

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_SEASON = {')
        for index, season in self.season.items():
            lines.append(f'    {index}: {season},')
        lines.append('}')
        return lines

    def write(self, file):
        print(f'writing {file}')
        with open(file, 'w', encoding='utf-8') as f:
            for text in self.encode():
                f.write(text + '\n')


class IslandSeasonalTaskExtractor(IslandSeasonExtractor):
    def __init__(self):
        super().__init__()
        self.task_list = []
        for season_id, season in self.season.items():
            self.task_list += season['task_list']
        print(self.task_list)
        self.task = {}
        data = LOADER.load('sharecfg/island_task_target.lua', keyword='pg.base.island_task_target')
        for index, item in data.items():
            if not isinstance(index, int):
                continue
            if item['id'] not in self.task_list:
                continue
            self.task[item['id']] = {
                'name': {
                    'cn': '',
                    'en': '',
                    'jp': '',
                    # 'tw': '',
                },
                'type': item['type'],
            }
            if isinstance(item['target_param'], dict):
                self.task[item['id']]['target'] = {item['target_param'][0]: item['target_num']}
            else:
                self.task[item['id']]['target'] = {}

        for index, name in self.extract_item_name('zh-CN').items():
            self.task[index]['name']['cn'] = name
        for index, name in self.extract_item_name('en-US').items():
            self.task[index]['name']['en'] = name
        for index, name in self.extract_item_name('ja-JP').items():
            self.task[index]['name']['jp'] = name
        # for index, name in self.extract_item_name('zh-TW').items():
        #     self.item[index]['name']['tw'] = name

    def extract_item_name(self, server):
        LOADER.server = server
        data = LOADER.load('sharecfg/island_task.lua', keyword='pg.base.island_task')
        out = {}
        index_shift = 10000
        for index, item in data.items():
            if not isinstance(index, int) or not item['target_id'][0] in self.task.keys():
                continue
            out[item['target_id'][0]] = item['name']

        return out

    def encode(self):
        lines = []
        lines.append('DIC_ISLAND_SEASONAL_TASK = {')
        for index, task in self.task.items():
            lines.append(f'    {index}: {task},')
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
        lines.append('DIC_ISLAND_RESTAURANT_RECIPE = {')
        for index, restaurant in self.restaurant.items():
            lines.append(f'    {index}: {restaurant},')
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
    lines.append('DIC_ISLAND_PASSIVE_RECIPE = {')
    lines.append('    1: {"refresh_times": ["03:00"], "product": {2606: 1}},')
    lines.append('    2: {"refresh_times": ["03:00"], "product": {2606: 1}},')
    lines.append('    3: {"refresh_times": ["03:00"], "product": {2606: 1}},')
    lines.append('    4: {"refresh_times": ["03:00"], "product": {2606: 1}},')
    lines.append('    5: {"refresh_times": ["03:00"], "product": {2606: 1}},')
    lines.append('    6: {"refresh_times": ["03:00"], "product": {2606: 1}},')
    lines.append('    1001: {"refresh_times": ["03:00"], "product": {4001: 4}},')
    lines.append('    1002: {"refresh_times": ["03:00"], "product": {4001: 4}},')
    lines.append('    1003: {"refresh_times": ["03:00"], "product": {4002: 8}},')
    lines.append('    1004: {"refresh_times": ["03:00"], "product": {4002: 8}},')
    lines.append('    1005: {"refresh_times": ["03:00"], "product": {4003: 12}},')
    lines.append('    1006: {"refresh_times": ["03:00"], "product": {4003: 12}},')
    lines.append('    1007: {"refresh_times": ["03:00"], "product": {4004: 3}},')
    lines.append('    1008: {"refresh_times": ["03:00"], "product": {4004: 3}},')
    lines.append('    40101: {"refresh_times": ["03:00", "18:00"], "product": {2700: 8}},')
    lines.append('    40102: {"refresh_times": ["03:00", "18:00"], "product": {2700: 8}},')
    lines.append('    40103: {"refresh_times": ["03:00", "18:00"], "product": {2700: 8}},')
    lines.append('    40104: {"refresh_times": ["03:00", "18:00"], "product": {2700: 8}},')
    lines.append('    40105: {"refresh_times": ["03:00", "18:00"], "product": {2700: 8}},')
    lines.append('    40106: {"refresh_times": ["03:00", "18:00"], "product": {2700: 8}},')
    lines.append('    40107: {"refresh_times": ["03:00", "18:00"], "product": {2700: 8}},')
    lines.append('    40108: {"refresh_times": ["03:00", "18:00"], "product": {2700: 8}},')
    lines.append('    40109: {"refresh_times": ["03:00", "18:00"], "product": {2700: 8}},')
    lines.append('    40201: {"refresh_times": ["03:00", "18:00"], "product": {2800: 8}},')
    lines.append('    40202: {"refresh_times": ["03:00", "18:00"], "product": {2800: 8}},')
    lines.append('    40203: {"refresh_times": ["03:00", "18:00"], "product": {2800: 8}},')
    lines.append('    40204: {"refresh_times": ["03:00", "18:00"], "product": {2800: 8}},')
    lines.append('    40205: {"refresh_times": ["03:00", "18:00"], "product": {2800: 8}},')
    lines.append('    40206: {"refresh_times": ["03:00", "18:00"], "product": {2800: 8}},')
    lines.append('    40207: {"refresh_times": ["03:00", "18:00"], "product": {2800: 8}},')
    lines.append('    40208: {"refresh_times": ["04:00", "18:00"], "product": {2800: 8}},')
    lines.append('    40209: {"refresh_times": ["04:00", "18:00"], "product": {2800: 8}},')
    lines.append('}')
    lines.append('')

    lines += IslandItemExtractor().encode()
    lines.append('')
    lines += IslandRecipeExtractor().encode()
    lines.append('')
    lines += IslandProductionExtractor().encode()
    lines.append('')
    lines += IslandShopItemExtractor().encode()
    lines.append('')
    lines += IslandSeasonExtractor().encode()
    lines.append('')
    lines += IslandSeasonalTaskExtractor().encode()
    lines.append('')
    lines += IslandRestaurantExtractor().encode()
    with open(save, 'w', encoding='utf-8') as f:
        for text in lines:
            f.write(text + '\n')
