"""Data and policy tests for island shop recognition and purchases."""
import pytest

import module.config.server as server
from module.island_handler.shop import IslandShop, ProductNameOcr


class FakeConfig:
    def __init__(self, values):
        self.values = values

    def cross_get(self, key, default=None):
        return self.values.get(key, default)


HARD_FLOOR = {'IslandProduction.IslandProduction.HardFloorItems': '{2000: 100, 5107: 3}'}


def make_shop(values=HARD_FLOOR):
    shop = object.__new__(IslandShop)
    shop.config = FakeConfig(values)
    return shop


@pytest.mark.parametrize(
    'srv, raw_name, expected_name, expected_id',
    [
        # 28 occurrences in the logs, the backslash is a stroke of the icon
        ('cn', '小\\麦种子', '小麦种子', 411000),
        # Noise seen around product names: prefix, repeated prefix, quote.
        ('cn', '_小麦种子', '小麦种子', 411000),
        ('cn', 'mm小麦种子', '小麦种子', 411000),
        ('cn', '小麦种子”', '小麦种子', 411000),
        # 丶 is the stroke of the first glyph of 小麦.
        ('cn', '小丶麦种子', '小麦种子', 411000),
        # Latin noise, as `m大米` in the recipe logs.
        ('cn', 'm小麦种子', '小麦种子', 411000),
        # 10 occurrences in the logs, the doubled prefix is read as one glyph.
        ('cn', '眸牛饲料', '哞哞牛饲料', 103002),
        # Latin names keep the space between words.
        ('en', '-Wheat  Seeds-', 'Wheat Seeds', 411000),
        ('tw', '_咯咯雞飼料', '咯咯雞飼料', 103000),
    ],
)
def test_product_name_cleanup_and_recipe_lookup(
    srv, raw_name, expected_name, expected_id, monkeypatch, caplog
):
    monkeypatch.setattr(server, 'server', srv)
    ocr = ProductNameOcr([])
    shop = make_shop()

    with caplog.at_level('INFO', logger='alas'):
        name = ocr.after_process(raw_name)
        recipe_id = shop.item_name_to_recipe_id(name)

    assert name == expected_name
    assert recipe_id == expected_id
    # Cleanup returns a real recipe name, so item_name_to_recipe_id needs no
    # edit-distance correction on the cleaned output.
    assert 'Corrected' not in caplog.text


@pytest.mark.parametrize(
    'srv, raw_name',
    [
        # Punctuation only, and an empty slot.
        ('cn', '”_.'),
        ('cn', '%'),
        ('cn', ''),
    ],
)
def test_product_name_cleanup_returns_empty_slot(srv, raw_name, monkeypatch):
    monkeypatch.setattr(server, 'server', srv)
    ocr = ProductNameOcr([])
    shop = make_shop()

    name = ocr.after_process(raw_name)

    assert name == ''
    assert shop.item_name_to_recipe_id(name) is None


class TestBuyWithItemCurrency:
    @staticmethod
    def make_shop(wheat):
        shop = make_shop()
        shop.island_shop_get_currency = lambda: {2000: wheat, 2001: 0, 2008: 0}
        shop.island_shop_item_ids = [103004]
        shop.bought = []
        shop.island_shop_buy_execute = lambda button, amount: shop.bought.append(amount)
        return shop

    def test_buy_above_hard_floor(self):
        shop = self.make_shop(130)
        # 5 flour cost 30 wheat, all above the hard floor of 100.
        assert shop.island_shop_buy_in_page(103004, 5)
        assert shop.bought == [5]

    def test_keep_hard_floor(self):
        shop = self.make_shop(130)
        # 6 flour cost 36 wheat, 6 of them below the hard floor.
        assert not shop.island_shop_buy_in_page(103004, 6)
        assert shop.bought == []
