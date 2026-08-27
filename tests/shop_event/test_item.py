"""Tests for CounterOcr.after_process in module.shop_event.item."""
import pytest

from module.shop_event.item import CounterOcr


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
    ])
    def test_fixup_documented_examples(self, raw, expected):
        """Documented examples in the fixup comment."""
        assert self.ocr.after_process(raw) == expected

    @pytest.mark.parametrize('raw, expected', [
        # "0100" -> "0/100", ..., "100100" -> "100/100", and likewise for
        # every other total in the fixup list
        (f'{current}{total}', f'{current}/{total}')
        for total in [100, 50, 30, 40, 20, 10, 5, 4, 2, 1]
        for current in range(0, total + 1)
    ])
    def test_fixup_range(self, raw, expected):
        """Every current in 0..total gets the slash inserted correctly."""
        assert self.ocr.after_process(raw) == expected

    @pytest.mark.parametrize('raw, expected', [
        # Edge case: OCR result is exactly the total, no slash is added
        ('100', '100'),
        ('50', '50'),
        ('30', '30'),
        ('40', '40'),
        ('20', '20'),
        ('10', '10'),
        ('5', '5'),
        ('4', '4'),
        ('2', '2'),
        ('1', '1'),
    ])
    def test_fixup_exact_total_unchanged(self, raw, expected):
        assert self.ocr.after_process(raw) == expected

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
