"""Tests for stock protected from island shop purchases and fish exchange."""
from module.island_handler.exchange import IslandExchange
from module.island_handler.shop import IslandShop


class FakeConfig:
    def __init__(self, values):
        self.values = values

    def cross_get(self, key, default=None):
        return self.values.get(key, default)


HARD_FLOOR = {'IslandProduction.IslandProduction.HardFloorItems': '{2000: 100, 5107: 3}'}


def make(cls, values):
    obj = object.__new__(cls)
    obj.config = FakeConfig(values)
    return obj


def test_protected_items():
    shop = make(IslandShop, HARD_FLOOR)
    assert shop.get_protected_items([2000, 2001]) == {2000: 100}


def test_protected_items_include_restaurant_reserve():
    values = dict(HARD_FLOOR, **{
        'IslandBusiness.IslandRestaurant.CafeGrade': 'bronze',
        'IslandBusiness.IslandRestaurant.CafeMenu': '{2000: 1}',
    })
    shop = make(IslandShop, values)
    # Bronze cafe without waitress reserves one shelf of 5 per menu dish
    assert shop.get_protected_items([2000]) == {2000: 105}


def test_fish_keep_items():
    exchange = make(IslandExchange, HARD_FLOOR)
    assert exchange.get_fish_keep_items() == {5107: 3}


class TestBuyWithItemCurrency:
    @staticmethod
    def make_shop(wheat):
        shop = make(IslandShop, HARD_FLOOR)
        shop.island_shop_get_currency = lambda: {2000: wheat, 2001: 0, 2008: 0}
        shop.island_shop_item_ids = [103004]
        shop.bought = []
        shop.island_shop_buy_execute = lambda button, amount: shop.bought.append(amount)
        return shop

    def test_buy_above_hard_floor(self):
        shop = self.make_shop(130)
        # 5 flour cost 30 wheat, all above the hard floor of 100
        assert shop.island_shop_buy_in_page(103004, 5)
        assert shop.bought == [5]

    def test_keep_hard_floor(self):
        shop = self.make_shop(130)
        # 6 flour cost 36 wheat, 6 of them below the hard floor
        assert not shop.island_shop_buy_in_page(103004, 6)
        assert shop.bought == []
