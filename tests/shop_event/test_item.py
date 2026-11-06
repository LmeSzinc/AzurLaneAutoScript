"""Tests for CounterOcr.after_process in module.shop_event.item."""
import pytest

from module.ocr.ocr import Ocr
from module.shop_event.item import CounterOcr, EventShopItem

AMBIGUOUS_SLASHLESS_COUNTERS = {'15', '015', '350', '0350', '1350', '2350', '3350', '4350'}


class TestCounterOcrAfterProcess:
    """Test the pure string post-processing of CounterOcr.after_process.

    after_process only rewrites the OCR result string (letter-to-digit
    revisions and the "55" -> "5/5" counter fixup), so the test calls the
    method directly on a CounterOcr instance without any image or OCR model
    involved.
    """

    ocr = CounterOcr([], name='Test_counter_ocr')

    @pytest.mark.parametrize('raw, expected', [
        # No revision needed
        ('14/15', '14/15'),
        ('0/1', '0/1'),
        ('0123456789/0123456789', '0123456789/0123456789'),
        ('', ''),
        # Single letter revision
        ('D', '0'),
        ('B', '8'),
        ('I', '1'),
        ('S', '5'),
        # Letters mixed with digits and each other
        ('I4/IS', '14/15'),
        ('DB/SB', '08/58'),
        ('IBS/DD', '185/00'),
        ('ISB', '158'),
        ('DS', '0/5'),
        ('I/D/S/B', '1/0/5/8'),
        ('IIDDSSBB', '11005588'),
        ('2B/2B', '28/28'),
        ('3I/D9', '31/09'),
    ])
    def test_letter_revision(self, raw, expected):
        """Letters are revised to digits, then the counter fixup applies."""
        assert self.ocr.after_process(raw) == expected

    @pytest.mark.parametrize('raw, expected', [
        ('55', '5/5'),
        ('2530', '25/30'),
        ('1515', '15/15'),
        ('350350', '350/350'),
        ('500500', '500/500'),
    ])
    def test_fixup_documented_examples(self, raw, expected):
        """Documented examples in the fixup comment."""
        assert self.ocr.after_process(raw) == expected

    @pytest.mark.parametrize('raw, expected', [
        # "0100" -> "0/100", ..., "100100" -> "100/100", and likewise for
        # every other total in the fixup list
        (f'{current}{total}', f'{current}/{total}')
        for total in [500, 350, 100, 50, 40, 30, 20, 15, 10, 5, 4, 2, 1]
        for current in range(0, total + 1)
        if f'{current}{total}' not in AMBIGUOUS_SLASHLESS_COUNTERS
    ])
    def test_fixup_range(self, raw, expected):
        """Every unambiguous current in 0..total gets the slash inserted correctly."""
        assert self.ocr.after_process(raw) == expected

    @pytest.mark.parametrize('raw, expected', [
        # Edge case: OCR result is exactly the total, no slash is added
        ('500', '500'),
        ('350', '350'),
        ('100', '100'),
        ('50', '50'),
        ('30', '30'),
        ('40', '40'),
        ('20', '20'),
        ('15', '15'),
        ('10', '10'),
        ('5', '5'),
        ('4', '4'),
        ('2', '2'),
        ('1', '1'),
    ])
    def test_fixup_exact_total_unchanged(self, raw, expected):
        assert self.ocr.after_process(raw) == expected

    @pytest.mark.parametrize('raw', sorted(AMBIGUOUS_SLASHLESS_COUNTERS))
    def test_fixup_ambiguous_counter_unchanged(self, raw):
        assert self.ocr.after_process(raw) == raw

    @pytest.mark.parametrize('raw, expected', [
        # Pure digits that do not end with any total stay unchanged
        ('77', '77'),
        ('233', '233'),
        ('68', '68'),
        ('93', '93'),
        ('813', '813'),
    ])
    def test_fixup_no_total_match(self, raw, expected):
        assert self.ocr.after_process(raw) == expected

    @pytest.mark.parametrize('raw, expected', [
        ('0/500', [0, 500]),
        ('500/500', [500, 500]),
        ('15/15', [15, 15]),
        ('14/15', [14, 15]),
    ])
    def test_parse_valid_counter(self, raw, expected):
        assert self.ocr.parse_result(raw) == expected

    @pytest.mark.parametrize('raw', [
        '', '/', '/500', '500/', '500', '500/50', '0/0', '1/2/3',
    ])
    def test_parse_invalid_counter(self, raw):
        assert self.ocr.parse_result(raw) == [0, 0]

    def test_ocr_invalid_counter_returns_sentinel(self, monkeypatch):
        monkeypatch.setattr(Ocr, 'ocr', lambda *args, **kwargs: ['/', '500/500'])

        assert self.ocr.ocr([None, None], direct_ocr=True) == [[0, 0], [500, 500]]


def test_price_135_total_15_is_equip_ssr():
    item = object.__new__(EventShopItem)
    item.price = 135
    item.total_count = 15
    item.name = 'Unknown'

    item.correct_name_and_cost()

    assert item.name == 'EquipSSR'
    assert item.cost == 'pt'


def make_ship_item(count, total_count, tag=None):
    item = object.__new__(EventShopItem)
    item.is_ship = True
    item.count = count
    item.total_count = total_count
    item.tag = tag
    return item


@pytest.mark.parametrize('count, total_count, tag, expected', [
    # The `unobtained` tag is a positive signal: present means the ship is
    # still locked, absent means there is nothing to unlock here.
    (5, 5, 'unobtained', True),
    (5, 5, None, False),
    (4, 5, None, False),
    (1, 1, 'unobtained', True),
    (0, 0, 'unobtained', True),
])
def test_is_unobtained_ship(count, total_count, tag, expected):
    assert make_ship_item(count, total_count, tag).is_unobtained_ship() is expected


@pytest.mark.parametrize('count, total_count, tag', [
    (5, 5, 'unobtained'),
    (3, 4, None),
    (1, 1, None),
])
def test_is_unobtained_ship_rejects_non_ship_items(count, total_count, tag):
    """An item priced without PT is not a ship, whatever its tag."""
    item = object.__new__(EventShopItem)
    item.is_ship = False
    item.count = count
    item.total_count = total_count
    item.tag = tag

    assert item.is_unobtained_ship() is False


@pytest.mark.parametrize('count, total_count, expected', [
    # Ships are stocked 5 at a time, so 4/5 proves a copy was already bought.
    (4, 5, True),
    (3, 5, True),
    (0, 5, True),
    (5, 5, False),
    # A total other than 5 is not trusted, it may be an OCR misread.
    (2, 3, False),
    (0, 1, False),
    (3, 10, False),
    (0, 0, False),
])
def test_is_partially_bought(count, total_count, expected):
    assert make_ship_item(count, total_count).is_partially_bought() is expected
