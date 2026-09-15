from types import SimpleNamespace

from module.island.utils import item_name
from module.island_handler.restaurant import IslandRestaurant, restaurant_item_log_text


class FakeConfig:
    def __init__(self, values):
        self.values = values

    def cross_get(self, key, default=None):
        return self.values.get(key, default)


def test_sell_plan_logs_configured_menu_and_actual_plan(caplog):
    restaurant = object.__new__(IslandRestaurant)
    restaurant.config = FakeConfig({
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


def test_unknown_ocr_item_keeps_detected_name():
    item = SimpleNamespace(id=0, name='UnknownTemplate', amount=3, tag=None)

    assert restaurant_item_log_text(item) == 'UnknownTemplate (stock 3)'
