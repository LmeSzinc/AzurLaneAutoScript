"""Restaurant recognition goldens, sell-plan reporting, and item formatting."""
from types import SimpleNamespace

from module.island.utils import item_name
from module.island_handler.restaurant import IslandRestaurant, restaurant_item_log_text
from module.testing.screenshot import image


class TestMenuJP:
    @image('island/restaurant/66ef9055', server='jp')
    def test_full_menu_without_event(self, main: IslandRestaurant):
        items = main.scan_item_grid(main.restaurant_grid)
        actual = dict(in_restaurant=main.is_in_island_restaurant(), has_event=main.restaurant_has_event,
                      offset_x=main._restaurant_offset_x, event_buff=main.event_buff, items=[dict(
                          id=item.id, name=item.name, amount=item.amount,
                          tag=item.tag, button=item.button) for item in items])
        regions = [(entry['button'], 'item #{} id={} amount={} tag={}'.format(
            index, entry['id'], entry['amount'], entry['tag']))
            for index, entry in enumerate(actual['items'])]
        main.device.review(actual, regions)
        assert actual == {
            'event_buff': 0,
            'has_event': False,
            'offset_x': 0,
            'in_restaurant': True,
            'items': [
                {
                    'amount': 14,
                    'button': (583, 208, 666, 295),
                    'id': 3108,
                    'name': 'Berry_and_Orange_Dessert',
                    'tag': None,
                },
                {
                    'amount': 19,
                    'button': (672, 208, 755, 295),
                    'id': 3028,
                    'name': 'Strawberry_Charlotte',
                    'tag': None,
                },
                {
                    'amount': 14,
                    'button': (762, 208, 845, 295),
                    'id': 3118,
                    'name': 'Paella',
                    'tag': None,
                },
                {
                    'amount': 14,
                    'button': (852, 208, 935, 295),
                    'id': 3107,
                    'name': 'Orchard_Duo',
                    'tag': None,
                },
                {
                    'amount': 36,
                    'button': (941, 208, 1024, 295),
                    'id': 3025,
                    'name': 'Sticky_Rice_with_Mango',
                    'tag': None,
                },
                {
                    'amount': 168,
                    'button': (583, 300, 666, 387),
                    'id': 3026,
                    'name': 'Banana_Crêpe',
                    'tag': None,
                },
                {
                    'amount': 24,
                    'button': (672, 300, 755, 387),
                    'id': 3023,
                    'name': 'Corn_Cup',
                    'tag': None,
                },
                {
                    'amount': 53,
                    'button': (762, 300, 845, 387),
                    'id': 3106,
                    'name': 'Succulently_Sweet',
                    'tag': None,
                },
                {
                    'amount': 53,
                    'button': (852, 300, 935, 387),
                    'id': 3009,
                    'name': 'Apple_Pie',
                    'tag': None,
                },
                {
                    'amount': 29,
                    'button': (941, 300, 1024, 387),
                    'id': 3024,
                    'name': 'Orange_Pie',
                    'tag': None,
                },
            ],
        }

    @image('island/restaurant/4ea8bdac', server='jp')
    def test_menu_with_event(self, main: IslandRestaurant):
        items = main.scan_item_grid(main.restaurant_grid)
        actual = dict(in_restaurant=main.is_in_island_restaurant(), has_event=main.restaurant_has_event,
                      offset_x=main._restaurant_offset_x, event_buff=main.event_buff, items=[dict(
                          id=item.id, name=item.name, amount=item.amount,
                          tag=item.tag, button=item.button) for item in items])
        regions = [(entry['button'], 'item #{} id={} amount={} tag={}'.format(
            index, entry['id'], entry['amount'], entry['tag']))
            for index, entry in enumerate(actual['items'])]
        main.device.review(actual, regions)
        assert actual == {
            'event_buff': 20,
            'has_event': True,
            'in_restaurant': True,
            'offset_x': 150,
            'items': [
                {
                    'amount': 46,
                    'button': (733, 208, 816, 295),
                    'id': 3010,
                    'name': 'Strawberry_Milkshake',
                    'tag': None,
                },
                {
                    'amount': 13,
                    'button': (822, 208, 905, 295),
                    'id': 3007,
                    'name': 'Latte',
                    'tag': None,
                },
                {
                    'amount': 8,
                    'button': (912, 208, 995, 295),
                    'id': 3111,
                    'name': 'Morning_Light_Energy_Combo',
                    'tag': None,
                },
                {
                    'amount': 14,
                    'button': (1002, 208, 1085, 295),
                    'id': 3008,
                    'name': 'Citrus_Coffee',
                    'tag': None,
                },
                {
                    'amount': 33,
                    'button': (1091, 208, 1174, 295),
                    'id': 3005,
                    'name': 'Iced_Coffee',
                    'tag': 'bonus',
                },
                {
                    'amount': 54,
                    'button': (733, 300, 816, 387),
                    'id': 3059,
                    'name': 'Omelette',
                    'tag': None,
                },
                {
                    'amount': 1,
                    'button': (822, 300, 905, 387),
                    'id': 3112,
                    'name': 'The_Wake-Up_Call',
                    'tag': None,
                },
                {
                    'amount': 1,
                    'button': (912, 300, 995, 387),
                    'id': 3006,
                    'name': 'Cheese',
                    'tag': None,
                },
                {
                    'amount': 7,
                    'button': (1002, 300, 1085, 387),
                    'id': 3113,
                    'name': 'Fruity_&_Fruitier',
                    'tag': None,
                },
            ],
        }

    @image('island/restaurant/a6e35620', server='jp')
    def test_partial_menu_without_event(self, main: IslandRestaurant):
        items = main.scan_item_grid(main.restaurant_grid)
        actual = dict(in_restaurant=main.is_in_island_restaurant(), has_event=main.restaurant_has_event,
                      offset_x=main._restaurant_offset_x, event_buff=main.event_buff, items=[dict(
                          id=item.id, name=item.name, amount=item.amount,
                          tag=item.tag, button=item.button) for item in items])
        regions = [(entry['button'], 'item #{} id={} amount={} tag={}'.format(
            index, entry['id'], entry['amount'], entry['tag']))
            for index, entry in enumerate(actual['items'])]
        main.device.review(actual, regions)
        assert actual == {
            'event_buff': 0,
            'has_event': False,
            'offset_x': 0,
            'in_restaurant': True,
            'items': [
                {
                    'amount': 7,
                    'button': (583, 208, 666, 295),
                    'id': 3104,
                    'name': 'Colorful_Fruit_Paradise',
                    'tag': None,
                },
                {
                    'amount': 50,
                    'button': (672, 208, 755, 295),
                    'id': 3017,
                    'name': 'Apple_Juice',
                    'tag': None,
                },
                {
                    'amount': 17,
                    'button': (762, 208, 845, 295),
                    'id': 3020,
                    'name': 'Strawberry_Lemon_Drink',
                    'tag': None,
                },
                {
                    'amount': 17,
                    'button': (852, 208, 935, 295),
                    'id': 3103,
                    'name': 'Floral_and_Fruity',
                    'tag': None,
                },
                {
                    'amount': 138,
                    'button': (941, 208, 1024, 295),
                    'id': 3021,
                    'name': 'Lavender_Tea',
                    'tag': None,
                },
                {
                    'amount': 3,
                    'button': (583, 300, 666, 387),
                    'id': 4014,
                    'name': 'Chrysanthemum_Tea',
                    'tag': None,
                },
                {
                    'amount': 10,
                    'button': (672, 300, 755, 387),
                    'id': 3018,
                    'name': 'Banana_and_Mango_Juice',
                    'tag': None,
                },
            ],
        }


class TestMenuCN:
    @image('island/restaurant/8a146fdb', server='cn')
    def test_items_when_restaurant_page_not_detected(self, main: IslandRestaurant):
        items = main.scan_item_grid(main.restaurant_grid)
        actual = dict(in_restaurant=main.is_in_island_restaurant(), has_event=main.restaurant_has_event,
                      offset_x=main._restaurant_offset_x, event_buff=main.event_buff, items=[dict(
                          id=item.id, name=item.name, amount=item.amount,
                          tag=item.tag, button=item.button) for item in items])
        regions = [(entry['button'], 'item #{} id={} amount={} tag={}'.format(
            index, entry['id'], entry['amount'], entry['tag']))
            for index, entry in enumerate(actual['items'])]
        main.device.review(actual, regions)
        assert actual == {
            'event_buff': 0,
            'has_event': False,
            'offset_x': 0,
            'in_restaurant': False,
            'items': [
                {
                    'amount': 4,
                    'button': (583, 208, 666, 295),
                    'id': 3120,
                    'name': "Buddha's_Temptation",
                    'tag': None,
                },
                {
                    'amount': 14,
                    'button': (672, 208, 755, 295),
                    'id': 3101,
                    'name': 'Classic_Tofu_Combo',
                    'tag': None,
                },
                {
                    'amount': 6,
                    'button': (762, 208, 845, 295),
                    'id': 3102,
                    'name': 'Hearty_Meal',
                    'tag': None,
                },
                {
                    'amount': 11,
                    'button': (852, 208, 935, 295),
                    'id': 3014,
                    'name': 'Cabbage_and_Tofu_Soup',
                    'tag': None,
                },
                {
                    'amount': 4,
                    'button': (941, 208, 1024, 295),
                    'id': 3013,
                    'name': 'Omurice',
                    'tag': None,
                },
                {
                    'amount': 23,
                    'button': (583, 300, 666, 387),
                    'id': 3011,
                    'name': 'Tofu',
                    'tag': None,
                },
                {
                    'amount': 26,
                    'button': (672, 300, 755, 387),
                    'id': 4039,
                    'name': 'Amaranth_Onigiri',
                    'tag': None,
                },
                {
                    'amount': 4,
                    'button': (762, 300, 845, 387),
                    'id': 3012,
                    'name': 'Tofu_with_Minced_Meat',
                    'tag': None,
                },
                {
                    'amount': 3,
                    'button': (852, 300, 935, 387),
                    'id': 4040,
                    'name': 'Tomato_and_Egg_Stir-Fry',
                    'tag': None,
                },
            ],
        }


class RestaurantConfig:
    def __init__(self, values):
        self.values = values

    def cross_get(self, key, default=None):
        return self.values.get(key, default)


class TestSellPlanReporting:
    def test_sell_plan_logs_configured_menu_and_actual_plan(self, caplog):
        restaurant = object.__new__(IslandRestaurant)
        restaurant.config = RestaurantConfig({
            'IslandBusiness.IslandRestaurant.KoiMenu': '3006: 2',
            'IslandProduction.IslandProduction.HardFloorItems': '',
            'IslandOrder.IslandOrder.StuckSeasonOrderId': 0,
        })
        restaurant.working_restaurant_id = 601
        restaurant.restaurant_capacity = {601: 6}
        restaurant.restaurant_quantity = {601: 1}
        restaurant.event_buff = 0
        restaurant.scan_all_items = lambda: [
            SimpleNamespace(id=3006, amount=6, price=90, tag=None),
        ]

        with caplog.at_level('INFO', logger='alas'):
            restaurant.get_sell_plan()

        name = item_name(3006)
        assert 'Restaurant configured menu' in caplog.text
        assert f'{name} (3006) x2' in caplog.text
        assert 'Restaurant sell plan' in caplog.text
        assert f'{name} (3006) (stock 6, sell 6)' in caplog.text

    def test_unknown_ocr_item_keeps_detected_name(self):
        item = SimpleNamespace(id=0, name='UnknownTemplate', amount=3, tag=None)

        assert restaurant_item_log_text(item) == 'UnknownTemplate (stock 3)'
