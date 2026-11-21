"""Protection policy tests owned by IslandShopUI."""
from module.island_handler.shop_ui import IslandShopUI


class FakeConfig:
    def __init__(self, values):
        self.values = values

    def cross_get(self, key, default=None):
        return self.values.get(key, default)


HARD_FLOOR = {'IslandProduction.IslandProduction.HardFloorItems': '{2000: 100, 5107: 3}'}


def make_ui(values):
    ui = object.__new__(IslandShopUI)
    ui.config = FakeConfig(values)
    return ui


def test_protected_items():
    ui = make_ui(HARD_FLOOR)
    assert ui.get_protected_items([2000, 2001]) == {2000: 100}


def test_protected_items_include_restaurant_reserve():
    values = dict(HARD_FLOOR, **{
        'IslandBusiness.IslandRestaurant.CafeGrade': 'bronze',
        'IslandBusiness.IslandRestaurant.CafeMenu': '{2000: 1}',
    })
    ui = make_ui(values)
    # Bronze cafe without waitress reserves one shelf of 5 per menu dish.
    assert ui.get_protected_items([2000]) == {2000: 105}
