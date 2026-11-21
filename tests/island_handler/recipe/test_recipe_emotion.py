from datetime import timedelta
from types import SimpleNamespace

import module.island_handler.recipe as recipe_module
from module.island_handler.recipe import (
    IslandRecipe,
    RECIPE_MODE_BUFFER_SURPLUS,
    RECIPE_MODE_IDLE_ACCUMULATING,
)


class FakeRecipe(IslandRecipe):
    def __init__(self, entries):
        self.recipe_id_sequence = list(entries)
        self.checked_recipe_modes = set()
        self.config = SimpleNamespace(ISLAND_IDLE_ACCUMULATING_DISPATCH_HOURS=100)
        self.calls = []

    def calculate_recipe_run_count(self, _info):
        return 99

    def calculate_buffer_surplus_run_count(self, _info):
        return 99

    def run_recipe(self, recipe_id, batch_count=float('inf'), mode=None):
        self.calls.append((recipe_id, batch_count, mode))
        return timedelta(minutes=1), batch_count

    def update_recipe_id_sequence_and_stock(self, recipe_id, _batch_count):
        self.recipe_id_sequence = [
            entry for entry in self.recipe_id_sequence if entry[0] != recipe_id
        ]


def entry(recipe_id, mode=None):
    return recipe_id, object(), mode


def test_finite_emotion_caps_batches_by_workload():
    recipe = FakeRecipe([entry(201005)])

    recipe.run(emotion=80)

    assert recipe.calls == [(201005, 6, None)]


def test_emotion_limit_does_not_increase_requested_batches():
    recipe = FakeRecipe([entry(201005)])
    recipe.calculate_recipe_run_count = lambda _info: 2

    recipe.run(emotion=80)

    assert recipe.calls == [(201005, 2, None)]


def test_emotion_budget_boundary_and_zero_budget():
    exact = FakeRecipe([entry(201002)])
    exact.run(emotion=24)
    assert exact.calls == [(201002, 1, None)]

    too_low = FakeRecipe([entry(201002)])
    assert too_low.run(emotion=23.999) is None
    assert too_low.calls == []

    zero = FakeRecipe([entry(201005)])
    assert zero.run(emotion=0) is None
    assert zero.calls == []


def test_production_limit_and_all_modes_still_apply():
    for mode in (None, RECIPE_MODE_BUFFER_SURPLUS, RECIPE_MODE_IDLE_ACCUMULATING):
        recipe = FakeRecipe([entry(201005, mode)])

        recipe.run(emotion=80)

        assert recipe.calls == [(201005, 6, mode)]


def test_unlimited_worker_keeps_existing_production_limit():
    recipe = FakeRecipe([entry(201002)])

    recipe.run()

    assert recipe.calls == [(201002, 5, None)]


def test_zero_workload_keeps_ordinary_limit(monkeypatch):
    recipe_id = 999001
    monkeypatch.setitem(
        recipe_module.DIC_ISLAND_RECIPE,
        recipe_id,
        {
            **recipe_module.DIC_ISLAND_RECIPE[101001],
            'workload': 0,
            'production_limit': 4,
        },
    )
    recipe = FakeRecipe([entry(recipe_id)])

    recipe.run(emotion=0)

    assert recipe.calls == [(recipe_id, 4, None)]


def test_unaffordable_recipe_is_skipped_without_poisoning_later_worker():
    recipe = FakeRecipe([entry(201002), entry(201005)])

    recipe.run(emotion=20)
    assert recipe.calls == [(201005, 1, None)]
    assert recipe.checked_recipe_modes == set()

    recipe.run(emotion=24)
    assert recipe.calls == [(201005, 1, None), (201002, 1, None)]
