"""Tests for fish production following the fish meat stock."""
import pytest

from module.island_handler.recipe import IslandRecipe, get_fish_meat_shortage_rate


class FakeConfig:
    def cross_get(self, key, default=None):
        return default


def make_recipe(fish_meat_stock=None):
    recipe = object.__new__(IslandRecipe)
    recipe.config = FakeConfig()
    if fish_meat_stock is not None:
        recipe.fish_meat_stock = fish_meat_stock
    # Yellowfin tuna, a saltwater fish, and catfish, a freshwater fish
    recipe.all_recipe_stocks = {201107: 0, 201002: 0}
    return recipe


def build_infos(recipe):
    recipe.get_recipe_id_sequence_to_run(
        daily_buffer_items_dict={2522: 18, 5107: 4, 5002: 4},
        hard_floor_items_dict={5107: 1},
        reserve_items_dict={},
        idle_accumulating_items_dict={},
        task_target_items_dict={},
    )
    return recipe.recipe_info_by_id


class TestFishMeatShortageRate:
    @pytest.mark.parametrize('meat_stock, rate', [
        (None, 1.),
        (0, 1.),
        (9, 0.5),
        (18, 0.),
        (399, 0.),
    ])
    def test_rate(self, meat_stock, rate):
        assert get_fish_meat_shortage_rate(meat_stock, 18, 18) == pytest.approx(rate)

    def test_meat_without_buffer(self):
        assert get_fish_meat_shortage_rate(0, 0, 0) == 1.


class TestFishTargetStock:
    def test_unknown_meat_stock_keeps_buffer(self):
        infos = build_infos(make_recipe())
        assert infos[201107].target_stock == 1 + 4
        assert infos[201002].target_stock == 4

    def test_enough_meat_keeps_only_hard_floor(self):
        infos = build_infos(make_recipe({2522: 399}))
        assert infos[201107].target_stock == 1
        assert infos[201107].daily_buffer == 0
        # Freshwater fish meat stock is unknown
        assert infos[201002].target_stock == 4

    def test_half_missing_meat_halves_buffer(self):
        infos = build_infos(make_recipe({2522: 9}))
        assert infos[201107].target_stock == 1 + 2
