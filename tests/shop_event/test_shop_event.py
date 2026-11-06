"""Tests for the ship handling of module.shop_event.shop_event.EventShop."""
import pytest

from module.shop_event.item import EventShopItem
from module.shop_event.shop_event import EventShop


def make_ship_item(count, total_count, tag='unobtained', price=8000):
    item = object.__new__(EventShopItem)
    item.name = 'ShipSSR'
    item.is_ship = True
    item.tag = tag
    item.count = count
    item.total_count = total_count
    item.price = price
    item.cost = 'pt'
    item.amount = 1
    return item


def make_normal_item(name, price, count, total_count, tag=None):
    item = object.__new__(EventShopItem)
    item.name = name
    item.is_ship = False
    item.tag = tag
    item.count = count
    item.total_count = total_count
    item.price = price
    item.cost = 'pt'
    item.amount = 1
    return item


class FakeEventShop:
    """The subset of EventShop that handle_unobtained_items touches."""

    def __init__(self, event_ended):
        self.is_event_ended = event_ended
        self.preserved = 0
        self.bought = []

    def preserve_pt(self, amount):
        self.preserved += amount

    def event_shop_buy_item(self, item, amount=None):
        self.bought.append((str(item), amount))


def handle(items, event_ended=True, buy_unobtained_items=True):
    shop = FakeEventShop(event_ended=event_ended)
    rest = EventShop.handle_unobtained_items(shop, items, buy_unobtained_items)
    return shop, rest


class TestShipFiltering:
    """handle_unobtained_items is the only place that decides which ships to buy."""

    def test_ship_without_unobtained_tag_is_not_bought(self):
        """An absent tag is not proof of ownership, only of nothing to unlock."""
        shop, rest = handle([make_ship_item(5, 5, tag=None)])

        assert shop.bought == []
        assert rest == []

    @pytest.mark.parametrize('count', [4, 3, 1, 0])
    def test_partially_bought_ship_is_not_bought(self, count):
        """A consumed counter means a copy was already bought in this event."""
        shop, rest = handle([make_ship_item(count, 5)])

        assert shop.bought == []
        assert rest == []

    def test_locked_ship_is_bought_once(self):
        shop, rest = handle([make_ship_item(5, 5)])

        assert shop.bought == [('ShipSSR_x1_5/5_pt_x8000_unobtained', 1)]
        # Returning the ship would let the filter buy duplicates of it.
        assert rest == []

    def test_stock_total_other_than_5_is_not_trusted(self):
        """An OCR misread of the total must not be taken for a bought copy."""
        shop, rest = handle([make_ship_item(2, 3)])

        assert shop.bought == [('ShipSSR_x1_2/3_pt_x8000_unobtained', 1)]
        assert rest == []

    def test_non_ship_items_are_returned_untouched(self):
        """Other items can share the 5/5 counter shape, e.g. Oil or Array."""
        items = [
            make_normal_item('BoxT4', 300, 3, 4),
            make_normal_item('Oil', 450, 5, 5),
            make_normal_item('Array', 1000, 2, 5),
        ]
        shop, rest = handle(items)

        assert rest == items
        assert shop.bought == []

    def test_only_unneeded_ships_are_dropped(self):
        untagged = make_ship_item(5, 5, tag=None)
        bought = make_ship_item(4, 5)
        locked = make_ship_item(5, 5)
        oil = make_normal_item('Oil', 450, 5, 5)

        shop, rest = handle([untagged, bought, locked, oil])

        assert rest == [oil]
        assert shop.bought == [(str(locked), 1)]


class TestUnlockBehaviour:
    """The unlock purchase respects the checkbox and the event deadline."""

    def test_pt_is_preserved_while_event_runs(self):
        shop, rest = handle([make_ship_item(5, 5)], event_ended=False)

        assert shop.bought == []
        assert shop.preserved == 8000
        assert rest == []

    def test_ship_is_dropped_when_checkbox_disabled(self):
        shop, rest = handle([make_ship_item(5, 5)], buy_unobtained_items=False)

        assert shop.bought == []
        assert rest == []

    def test_non_ship_items_survive_while_event_runs(self):
        oil = make_normal_item('Oil', 450, 5, 5)
        shop, rest = handle([make_ship_item(5, 5), oil], event_ended=False)

        assert rest == [oil]
        assert shop.preserved == 8000
