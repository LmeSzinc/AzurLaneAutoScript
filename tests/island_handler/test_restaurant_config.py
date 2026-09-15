"""Tests for restaurant configuration helpers."""
import pytest

from module.exception import RequestHumanTakeover
from module.island_handler.restaurant_config import (
    get_menu_reserve_items,
    normalize_waitress_slots,
)


class FakeConfig:
    def __init__(self, values):
        self.values = values

    def cross_get(self, key, default=None):
        return self.values.get(key, default)


PREFIX = 'IslandBusiness.IslandRestaurant.'


class TestGetMenuReserveItems:
    def test_reserves_full_capacity_tranche(self):
        """A menu dish reserves the whole shelf capacity, not its daily rate.

        The restaurant only lists a dish once a full capacity tranche is in
        stock and sells it all at once (see has_sellable_capacity), so a dish
        planned at e.g. 0.667/day must still accumulate a full tranche or it
        would never become sellable.
        """
        config = FakeConfig({
            PREFIX + 'KoiGrade': 'gold',
            PREFIX + 'KoiWaitress1': 'Chao_Ho',
            # 3011 sells below capacity per day, 3012 at full capacity
            PREFIX + 'KoiMenu': '{3011: 0.667, 3012: 7}',
        })
        # Koi gold: initial capacity 6, Chao_Ho +1
        assert get_menu_reserve_items(config) == {3011: 7, 3012: 7}

    def test_zero_amount_not_reserved(self):
        config = FakeConfig({
            PREFIX + 'KoiGrade': 'gold',
            PREFIX + 'KoiWaitress1': 'Chao_Ho',
            PREFIX + 'KoiMenu': '{3011: 0}',
        })
        assert get_menu_reserve_items(config) == {}

    def test_empty_menus_reserve_nothing(self):
        assert get_menu_reserve_items(FakeConfig({})) == {}


class TestNormalizeWaitressSlots:
    @pytest.mark.parametrize(('values', 'message'), [
        (['Unknown'], 'Invalid waitress value for restaurant 601: Unknown'),
        (['Chao_Ho', 'Chao_Ho'], 'Duplicate named waitress for restaurant 601: Chao_Ho'),
        (['none', 'any', 'none'], 'Restaurant 601 has more than two waitress slots'),
    ])
    def test_logs_error_before_requesting_human_takeover(self, caplog, values, message):
        with caplog.at_level('ERROR', logger='alas'):
            with pytest.raises(RequestHumanTakeover) as exc_info:
                normalize_waitress_slots(601, values)

        assert str(exc_info.value) == message
        assert caplog.messages[-1] == message
