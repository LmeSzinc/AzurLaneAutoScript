"""General shop selection regressions; no device interaction or purchases."""
import re
import unittest
from contextlib import contextmanager
from types import SimpleNamespace

from module.config.deep import deep_get, deep_set

from module.shop.base import FILTER_REGEX
from module.shop.shop_general import GeneralShop_250814
from module.statistics.item import Item


class MemoryConfig(SimpleNamespace):
    def update(self):
        pass

    @contextmanager
    def multi_set(self):
        yield self

    def cross_get(self, keys, default=None):
        return deep_get(self.data, keys=keys, default=default)

    def cross_set(self, keys, value):
        deep_set(self.data, keys=keys, value=value)
        prefix = 'ShopFrequent.GeneralShop.'
        if keys.startswith(prefix):
            setattr(self, 'GeneralShop_' + keys[len(prefix):], value)


def make_shop(slots='1', buy_skin=True, consume=False, coins=100000,
              item_filter='BookRedT3 > BoxIrisT2 > BoxT4', use_gems=False):
    # Avoid constructing a device/config file; exercise the real selection chain.
    shop = GeneralShop_250814.__new__(GeneralShop_250814)
    shop.config = MemoryConfig(
        GeneralShop_SkinBoxSlots=slots,
        GeneralShop_SkinBoxPurchaseLimit=0,
        GeneralShop_SkinBoxPurchaseCount=0,
        task=SimpleNamespace(command='ShopFrequent'),
        data={},
        GeneralShop_BuySkinBox=buy_skin,
        GeneralShop_ConsumeCoins=consume,
        GeneralShop_UseGems=use_gems,
        GeneralShop_Filter=item_filter,
    )
    shop._currency = coins
    shop.gems = 10000
    return shop


def make_item(shop, slot=(0, 0), name='1', cost='Coins', price=7000, amount=1):
    # These are the fields produced by ItemGrid.predict(), without loading images.
    item = Item.__new__(Item)
    item._button = shop.shop_grid[slot]
    item.name = name
    item.cost = cost
    item.price = price
    item.amount = amount
    item.tag = None
    match = re.search(FILTER_REGEX, item.name)
    item.group, item.sub_genre, item.tier = (
        [value.lower() if value is not None else None for value in match.groups()]
        if match else (None, None, None)
    )
    return item


class TestGeneralShopSkinBoxSlots(unittest.TestCase):
    def test_multi_select_uses_static_row_major_positions(self):
        shop = make_shop(slots='2,6,10')
        items = [make_item(shop, slot=(x, y), name=str(1 + x + 5 * y))
                 for y in range(2) for x in range(5)]
        for index, item in enumerate(items, start=1):
            with self.subTest(slot=index):
                self.assertIs(shop.shop_get_item_to_buy([item]), item if index in (2, 6, 10) else None)

    def test_selected_position_is_not_detected_list_index(self):
        shop = make_shop(slots=2)
        second = make_item(shop, slot=(1, 0), name='2')
        last = make_item(shop, slot=(4, 1), name='10')
        self.assertIs(shop.shop_get_item_to_buy([last, second]), second)
        self.assertIsNone(shop.shop_get_item_to_buy([last]))

    def test_none_blocks_skin_boxes_but_keeps_ordinary_filter(self):
        shop = make_shop(slots='none', consume=True, coins=550000)
        skin = make_item(shop)
        ordinary = make_item(shop, slot=(2, 1), name='BookRedT3', price=2400)
        self.assertIs(shop.shop_get_item_to_buy([skin, ordinary]), ordinary)

    def test_invalid_positions_fail_closed_for_skin_boxes_only(self):
        for slots in ('2,bad', '0', '11', True, '()', '', None):
            with self.subTest(slots=slots):
                shop = make_shop(slots=slots, consume=True, coins=550000)
                skin = make_item(shop)
                ordinary = make_item(shop, slot=(2, 1), name='BookRedT3', price=2400)
                self.assertIs(shop.shop_get_item_to_buy([skin, ordinary]), ordinary)

    def test_default_retains_legacy_unknown_box_purchase(self):
        shop = make_shop(slots='all')
        rerun = make_item(shop, slot=(1, 0))
        self.assertIs(shop.shop_get_item_to_buy([rerun]), rerun)

    def test_default_retains_known_box_filter(self):
        shop = make_shop(slots='all', buy_skin=False)
        support = make_item(shop, slot=(1, 0), name='BoxIrisT2', price=900)
        self.assertIs(shop.shop_get_item_to_buy([support]), support)

    def test_default_all_retains_known_box_price_behavior(self):
        shop = make_shop(slots='all', buy_skin=False)
        discounted = make_item(shop, slot=(1, 0), name='BoxIrisT2', price=6300)
        self.assertIs(shop.shop_get_item_to_buy([discounted]), discounted)

    def test_default_retains_overflow_purchase(self):
        shop = make_shop(slots='all', buy_skin=False, consume=True, coins=550000)
        rerun = make_item(shop, slot=(1, 0))
        self.assertIs(shop.shop_get_item_to_buy([rerun]), rerun)

    def test_unknown_box_only_at_fixed_first_slot(self):
        shop = make_shop()
        first = make_item(shop)
        rerun = make_item(shop, slot=(1, 0), name='2')
        self.assertIs(shop.shop_get_item_to_buy([rerun, first]), first)

    def test_all_other_slots_rejected(self):
        shop = make_shop()
        for y in range(2):
            for x in range(5):
                if (x, y) == (0, 0):
                    continue
                with self.subTest(slot=(x, y)):
                    rerun = make_item(shop, slot=(x, y))
                    self.assertIsNone(shop.shop_get_item_to_buy([rerun]))

    def test_sold_out_first_slot_does_not_fall_back(self):
        shop = make_shop()
        # The detector omits sold-out slots, leaving this as items[0].
        rerun = make_item(shop, slot=(1, 0))
        self.assertIsNone(shop.shop_get_item_to_buy([rerun]))

    def test_non_skin_first_slot_does_not_move_skin_selection(self):
        shop = make_shop()
        ordinary = make_item(shop, name='BookRedT3', price=2400)
        rerun = make_item(shop, slot=(1, 0))
        self.assertIs(shop.shop_get_item_to_buy([ordinary, rerun]), ordinary)

    def test_repeated_scan_after_first_purchase_does_not_buy_rerun(self):
        shop = make_shop()
        first = make_item(shop)
        rerun = make_item(shop, slot=(1, 0), name='2')
        self.assertIs(shop.shop_get_item_to_buy([first, rerun]), first)
        for _ in range(3):
            self.assertIsNone(shop.shop_get_item_to_buy([rerun]))

    def test_refresh_restocking_fixed_first_slot_can_be_bought(self):
        shop = make_shop()
        first = make_item(shop)
        self.assertIs(shop.shop_get_item_to_buy([first]), first)
        self.assertIsNone(shop.shop_get_item_to_buy([]))
        restocked = make_item(shop, name='3')
        self.assertIs(shop.shop_get_item_to_buy([restocked]), restocked)

    def test_known_support_crate_in_first_slot_follows_filter(self):
        shop = make_shop(buy_skin=False)
        first = make_item(shop, name='BoxIrisT2', price=900)
        self.assertIs(shop.shop_get_item_to_buy([first]), first)

    def test_known_support_crates_outside_skin_slots_allow_overflow(self):
        # These are ordinary research-support crates, not cosmetic boxes.
        # Sardegna has no named selector on dev, so use its existing overflow path.
        shop = make_shop(buy_skin=False, consume=True, coins=550000)
        for name in ('BoxIrisT2', 'BoxSardegnaT2'):
            with self.subTest(name=name):
                support = make_item(shop, slot=(1, 0), name=name, price=900)
                self.assertIs(shop.shop_get_item_to_buy([support]), support)

    def test_known_support_crate_outside_skin_slots_follows_filter(self):
        shop = make_shop(buy_skin=False)
        support = make_item(shop, slot=(1, 0), name='BoxIrisT2', price=900)
        self.assertIs(shop.shop_get_item_to_buy([support]), support)

    def test_generic_box_filter_retains_known_support_crate(self):
        shop = make_shop(item_filter='Box', buy_skin=False)
        support = make_item(shop, slot=(1, 0), name='BoxIrisT2', price=900)
        self.assertIs(shop.shop_get_item_to_buy([support]), support)

    def test_overflow_cannot_bypass_skin_position_rule(self):
        shop = make_shop(consume=True, coins=550000, buy_skin=False)
        for name in ('1', '2', '3'):
            with self.subTest(name=name):
                rerun = make_item(shop, slot=(1, 0), name=name)
                self.assertIsNone(shop.shop_get_item_to_buy([rerun]))

    def test_known_support_crate_price_currency_and_amount_are_not_skin_gated(self):
        shop = make_shop(slots='none', consume=False, use_gems=True)
        for cost, price, amount in (('Coins', 900, 1), ('Gems', 7000, 1),
                                    ('Coins', 6300, 1), ('Coins', 7000, 1),
                                    ('Coins', 7001, 1), ('Coins', 7000, 2)):
            with self.subTest(cost=cost, price=price, amount=amount):
                support = make_item(shop, slot=(1, 0), name='BoxIrisT2',
                                    cost=cost, price=price, amount=amount)
                self.assertIs(shop.shop_get_item_to_buy([support]), support)

    def test_unknown_box_requires_original_skin_signature(self):
        shop = make_shop()
        for cost, price, amount in (('Gems', 7000, 1), ('Coins', 6300, 1),
                                    ('Coins', 7000, 2)):
            with self.subTest(cost=cost, price=price, amount=amount):
                first = make_item(shop, cost=cost, price=price, amount=amount)
                self.assertIsNone(shop.shop_get_item_to_buy([first]))

    def test_unknown_other_price_retains_ordinary_overflow_behavior(self):
        # No evidence identifies this as a skin box, so leave overflow unchanged.
        shop = make_shop(consume=True, coins=550000)
        ordinary = make_item(shop, slot=(1, 0), price=2000)
        self.assertIs(shop.shop_get_item_to_buy([ordinary]), ordinary)

    def test_known_ordinary_technology_boxes_not_restricted(self):
        for name in ('BoxT1', 'BoxT2', 'BoxT3', 'BoxT4', 'BoxT5'):
            with self.subTest(name=name):
                shop = make_shop(item_filter='Box', buy_skin=False)
                ordinary = make_item(shop, slot=(1, 0), name=name)
                self.assertIs(shop.shop_get_item_to_buy([ordinary]), ordinary)

    def test_ordinary_book_in_other_slot_still_follows_filter(self):
        shop = make_shop()
        ordinary = make_item(shop, slot=(2, 1), name='BookRedT3', price=2400)
        rerun = make_item(shop, slot=(1, 0))
        self.assertIs(shop.shop_get_item_to_buy([rerun, ordinary]), ordinary)

    def test_overflow_still_selects_ordinary_goods(self):
        shop = make_shop(consume=True, coins=550000)
        ordinary = make_item(shop, slot=(2, 1), name='PlateGeneralT3', price=3000)
        rerun = make_item(shop, slot=(1, 0))
        self.assertIs(shop.shop_get_item_to_buy([rerun, ordinary]), ordinary)

    def test_buy_skin_disabled_does_not_auto_buy_unknown_first(self):
        shop = make_shop(buy_skin=False)
        self.assertIsNone(shop.shop_get_item_to_buy([make_item(shop)]))

    def test_insufficient_coins_does_not_select_unknown_first(self):
        shop = make_shop(coins=6999)
        self.assertIsNone(shop.shop_get_item_to_buy([make_item(shop)]))

    def test_insufficient_coins_still_blocks_ordinary_support_crate(self):
        shop = make_shop(coins=899)
        self.assertIsNone(shop.shop_get_item_to_buy([make_item(shop, name='BoxIrisT2', price=900)]))


if __name__ == '__main__':
    unittest.main()
