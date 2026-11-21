"""Tests for EventShopUI._get_event_deadline in module.shop_event.ui."""
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import module.shop_event.ui as ui_module
from module.shop_event.ui import EventShopUI

IMAGE = object()


class FrozenDatetime(datetime):
    """datetime whose now() returns a fixed time, set per test."""
    frozen_now = datetime(2026, 8, 20, 12, 0, 0)

    @classmethod
    def now(cls, tz=None):
        return cls.frozen_now


@pytest.fixture
def get_deadline(monkeypatch):
    """
    Returns a function (raw, now) -> deadline.
    OCR_EVENT_SHOP_DEADLINE.ocr is mocked to return `raw`,
    "now" is frozen and the server timezone offset is zero.
    """
    ocr = Mock()
    monkeypatch.setattr(ui_module.OCR_EVENT_SHOP_DEADLINE, 'ocr', ocr)
    monkeypatch.setattr(ui_module, 'datetime', FrozenDatetime)
    monkeypatch.setattr(ui_module, 'server_time_offset', lambda: timedelta(0))
    ui = SimpleNamespace(device=SimpleNamespace(image=IMAGE))

    def run(raw, now=datetime(2026, 8, 20, 12, 0, 0)):
        FrozenDatetime.frozen_now = now
        ocr.return_value = raw
        result = EventShopUI._get_event_deadline(ui)
        ocr.assert_called_once_with(IMAGE)
        return result

    return run


class TestExplicitYear:
    def test_cn_format(self, get_deadline):
        # 23:59:59 + 1s -> midnight of the next day
        assert get_deadline(':2026.8.13~2026.9.323:59:59') == datetime(2026, 9, 4, 0, 0, 0)

    def test_custom_end_time(self, get_deadline):
        assert get_deadline(':2026.8.13~2026.9.314:59:59') == datetime(2026, 9, 3, 15, 0, 0)

    def test_missing_time_assumes_end_of_day(self, get_deadline):
        assert get_deadline(':2026.8.13~2026.9.3') == datetime(2026, 9, 4, 0, 0, 0)

    def test_trailing_whitespace_after_time(self, get_deadline):
        assert get_deadline(':2026.8.13~2026.9.323:59:59 ') == datetime(2026, 9, 4, 0, 0, 0)

    def test_uses_last_date_as_deadline(self, get_deadline):
        assert get_deadline('2026.1.1~2026.2.2~2026.3.323:59:59') == datetime(2026, 3, 4, 0, 0, 0)

    def test_year_far_from_now_is_not_constrained(self, get_deadline):
        """The 90 days constraint only applies to guessed years."""
        result = get_deadline(':2030.1.1~2030.2.123:59:59', now=datetime(2026, 1, 1))
        assert result == datetime(2030, 2, 2, 0, 0, 0)

    def test_invalid_date(self, get_deadline):
        assert get_deadline(':2026.1.1~2026.2.3023:59:59') is None


class TestGuessedYear:
    def test_en_format_without_year(self, get_deadline):
        # EN shop during 1st capsule rerun
        result = get_deadline(':10.8-10.2214:59:59', now=datetime(2026, 10, 15, 12, 0, 0))
        assert result == datetime(2026, 10, 22, 15, 0, 0)

    def test_year_rollover_picks_next_year(self, get_deadline):
        result = get_deadline(':12.1-1.523:59:59', now=datetime(2026, 12, 28))
        assert result == datetime(2027, 1, 6, 0, 0, 0)

    def test_year_rollover_picks_previous_year(self, get_deadline):
        result = get_deadline(':12.1-1.523:59:59', now=datetime(2027, 1, 10))
        assert result == datetime(2027, 1, 6, 0, 0, 0)

    def test_missing_time_without_year(self, get_deadline):
        result = get_deadline(':10.8-10.22', now=datetime(2026, 10, 15))
        assert result == datetime(2026, 10, 23, 0, 0, 0)

    def test_closest_is_far_falls_back_to_current_year(self, get_deadline):
        """Closest candidate is 2025-09-30 (152 days away), violates 90 days, use 2026."""
        result = get_deadline(':9.1-9.3023:59:59', now=datetime(2026, 3, 1))
        assert result == datetime(2026, 10, 1, 0, 0, 0)

    def test_exactly_90_days_is_accepted(self, get_deadline):
        deadline = datetime(2027, 1, 5, 23, 59, 59)
        now = deadline - timedelta(days=90)
        result = get_deadline(':10.1-1.523:59:59', now=now)
        assert result == datetime(2027, 1, 6, 0, 0, 0)

    def test_over_90_days_falls_back_to_current_year(self, get_deadline):
        deadline = datetime(2027, 1, 5, 23, 59, 59)
        now = deadline - timedelta(days=90, seconds=1)
        result = get_deadline(':10.1-1.523:59:59', now=now)
        assert result == datetime(2026, 1, 6, 0, 0, 0)

    def test_leap_day_ok(self, get_deadline):
        result = get_deadline(':2.1~2.2923:59:59', now=datetime(2028, 2, 10))
        assert result == datetime(2028, 3, 1, 0, 0, 0)

    def test_leap_day_without_valid_year(self, get_deadline):
        """2025, 2026, 2027 all have no Feb 29."""
        assert get_deadline(':2.1~2.2923:59:59', now=datetime(2026, 2, 20)) is None

    def test_leap_day_far_and_current_year_invalid(self, get_deadline):
        """Closest is 2028-02-29 but >90 days away; fallback 2027-02-29 is invalid."""
        assert get_deadline(':2.1~2.2923:59:59', now=datetime(2027, 10, 1)) is None


class TestUnreadable:
    @pytest.mark.parametrize('raw', [
        '',
        'garbage',
        ':2026.9.3',  # only one date
        ':2026.9.323:59:59',  # only one date with time
        '12345',
    ])
    def test_returns_none(self, get_deadline, raw):
        assert get_deadline(raw) is None