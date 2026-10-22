from module.island_handler.recipe import (
    IslandRecipe,
    RECIPE_MODE_BUFFER_SURPLUS,
    RECIPE_MODE_IDLE_ACCUMULATING,
    RecipeInfo,
)


CONFIG_PATH = 'IslandProduction.IslandProduction.SkipBufferSurplus'


class FakeConfig:
    def __init__(self, values=None):
        self.values = values or {}

    def cross_get(self, key, default=None):
        return self.values.get(key, default)


class NoBufferSurplusCheckRecipe(IslandRecipe):
    @staticmethod
    def calculate_buffer_surplus_run_count(_info):
        raise AssertionError('buffer-surplus eligibility should not be checked')


def make_recipe(
        recipe_id, info, checked_modes=(), skip_buffer_surplus=None,
        recipe_class=IslandRecipe,
):
    recipe = object.__new__(recipe_class)
    values = {} if skip_buffer_surplus is None else {CONFIG_PATH: skip_buffer_surplus}
    recipe.config = FakeConfig(values)
    recipe.recipe_info_by_id = {recipe_id: info}
    recipe.checked_recipe_modes = set(checked_modes)
    return recipe


def test_buffer_surplus_is_skipped_by_default(caplog):
    info = RecipeInfo(162, 162, 162, 162, [], 1)
    recipe = make_recipe(101001, info, recipe_class=NoBufferSurplusCheckRecipe)

    with caplog.at_level('INFO', logger='alas'):
        assert recipe._build_recipe_id_sequence_to_run() == [
            (101001, info, RECIPE_MODE_IDLE_ACCUMULATING),
        ]

    assert 'Skip buffer-surplus recipe checks' in caplog.text


def test_buffer_surplus_can_be_enabled():
    info = RecipeInfo(162, 162, 162, 162, [], 1)
    recipe = make_recipe(
        101001,
        info,
        skip_buffer_surplus=False,
    )

    assert recipe._build_recipe_id_sequence_to_run() == [
        (101001, info, RECIPE_MODE_BUFFER_SURPLUS),
    ]


def test_idle_accumulating_follows_failed_buffer_surplus():
    info = RecipeInfo(162, 162, 162, 162, [], 1)
    recipe = make_recipe(
        101001,
        info,
        checked_modes=[(101001, RECIPE_MODE_BUFFER_SURPLUS)],
        skip_buffer_surplus=False,
    )

    assert recipe._build_recipe_id_sequence_to_run() == [
        (101001, info, RECIPE_MODE_IDLE_ACCUMULATING),
    ]


def test_hard_floor_shortfall_runs_first():
    # Half way to its hard floor, so less urgent than both other entries by
    # demand and buffer fill level
    below_floor = RecipeInfo(2, 4, 0, 2, [], 0, 4)
    buffer_short = RecipeInfo(0, 20, 20, 8, [], 0)
    task_target = RecipeInfo(0, 0, 0, 12, [(24, 1)], 0)
    recipe = make_recipe(201002, below_floor)
    recipe.recipe_info_by_id.update({201006: buffer_short, 201005: task_target})

    sequence = recipe._build_recipe_id_sequence_to_run()

    assert [recipe_id for recipe_id, _info, _mode in sequence] == [201002, 201005, 201006]


def test_hard_floor_met_keeps_normal_order():
    floor_met = RecipeInfo(1, 11, 10, 2, [], 0, 1)
    task_target = RecipeInfo(0, 20, 20, 8, [(30, 1)], 0)
    recipe = make_recipe(201002, floor_met)
    recipe.recipe_info_by_id[201006] = task_target

    sequence = recipe._build_recipe_id_sequence_to_run()

    assert [recipe_id for recipe_id, _info, _mode in sequence] == [201006, 201002]
