"""Tests for the island shop product name OCR cleanup.

The misreads are taken from user logs of the island production task, where
cnocr read a fragment of the item icon or the stroke of the next glyph as an
extra character and the shop scanned the same page forever.
"""
from types import SimpleNamespace

import pytest

import module.config.server as server
import module.ocr.ocr as ocr_module
from module.island_handler.shop import IslandShop, ProductNameOcr


class FakeCnocrModel:
    """Stands in for the cnocr model and returns canned lines."""

    def __init__(self, lines):
        self.lines = list(lines)

    def atomic_ocr_for_single_lines(self, image_list, alphabet=None):
        assert len(image_list) == len(self.lines)
        return [list(line) for line in self.lines]


def shop_with_ocr(lines, monkeypatch):
    """Build an IslandShop whose item name OCR reads the given lines."""
    shop = object.__new__(IslandShop)
    shop.device = SimpleNamespace(image=None)
    button_count = len(shop._island_shop_item_name_grid.buttons)
    model = FakeCnocrModel(list(lines) + [''] * (button_count - len(lines)))
    monkeypatch.setattr(ProductNameOcr, 'cnocr', property(lambda self: model))
    # The image is not used by the mocked model
    monkeypatch.setattr(ProductNameOcr, 'pre_process', lambda self, image: image)
    monkeypatch.setattr(ocr_module, 'crop', lambda image, area, copy=True: None)
    return shop


def read_ids(shop):
    names = shop._island_shop_item_name_ocr.ocr(shop.device.image)
    ids = [shop.item_name_to_recipe_id(name) for name in names]
    return names, ids


@pytest.mark.parametrize(
    'srv, raw_name, expected_name, expected_id',
    [
        # 28 occurrences in the logs, the backslash is a stroke of the icon
        ('cn', '小\\麦种子', '小麦种子', 411000),
        # noise seen around product names: prefix, repeated prefix, quote
        ('cn', '_小麦种子', '小麦种子', 411000),
        ('cn', 'mm小麦种子', '小麦种子', 411000),
        ('cn', '小麦种子”', '小麦种子', 411000),
        # 丶 is the stroke of the first glyph of 小麦
        ('cn', '小丶麦种子', '小麦种子', 411000),
        # latin noise, as `m大米` in the recipe logs
        ('cn', 'm小麦种子', '小麦种子', 411000),
        # 10 occurrences in the logs, the doubled prefix is read as one glyph
        ('cn', '眸牛饲料', '哞哞牛饲料', 103002),
        # latin names keep the space between words
        ('en', '-Wheat  Seeds-', 'Wheat Seeds', 411000),
        ('tw', '_咯咯雞飼料', '咯咯雞飼料', 103000),
    ],
)
def test_name_is_cleaned(srv, raw_name, expected_name, expected_id, monkeypatch, caplog):
    monkeypatch.setattr(server, 'server', srv)
    shop = shop_with_ocr([raw_name], monkeypatch)

    with caplog.at_level('INFO', logger='alas'):
        names, ids = read_ids(shop)

    assert names[0] == expected_name
    assert ids[0] == expected_id
    # the real name is returned, so no edit distance correction is needed
    assert 'Corrected' not in caplog.text


@pytest.mark.parametrize(
    'srv, raw_name',
    [
        # punctuation only, and an empty slot
        ('cn', '”_.'),
        ('cn', '%'),
        ('cn', ''),
    ],
)
def test_noise_only_slot_returns_none(srv, raw_name, monkeypatch):
    monkeypatch.setattr(server, 'server', srv)
    shop = shop_with_ocr([raw_name], monkeypatch)

    names, ids = read_ids(shop)

    assert names[0] == ''
    assert ids[0] is None


@pytest.mark.parametrize(
    'lines, expected_ids',
    [
        (['', '%', '小\\麦种子'], [None, None, 411000]),
    ],
)
def test_slots_keep_their_position(lines, expected_ids, monkeypatch):
    monkeypatch.setattr(server, 'server', 'cn')
    shop = shop_with_ocr(lines, monkeypatch)

    names, ids = read_ids(shop)

    assert len(ids) == len(shop._island_shop_item_name_grid.buttons)
    assert ids[:len(expected_ids)] == expected_ids
