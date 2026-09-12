"""Tests for restaurant menu reserve derivation."""
from module.island_handler.restaurant_config import get_menu_reserve_items


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
