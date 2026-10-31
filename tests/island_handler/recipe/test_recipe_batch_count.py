"""Recipe amount selection with and without the MAX control."""
from types import SimpleNamespace

import pytest

from module.exception import GameTooManyClickError
import module.island_handler.recipe as recipe_module
from module.island_handler.recipe import IslandRecipe


def make_recipe(monkeypatch, amount=1, maximum=8, max_available=True):
    main = object.__new__(IslandRecipe)
    state = SimpleNamespace(amount=amount, max_clicks=0, adjustments=[])
    main.device = SimpleNamespace(image=object(), screenshot=lambda: None)

    def click_max(button, **kwargs):
        assert button is recipe_module.ISLAND_RECIPE_AMOUNT_MAX
        assert max_available, 'MAX must not be needed for a single batch'
        state.max_clicks += 1
        state.amount = maximum
        return True

    def adjust(button, n, **kwargs):
        state.adjustments.append((button, n))
        if button is recipe_module.ISLAND_RECIPE_AMOUNT_MINUS:
            state.amount = max(1, state.amount - n)
        else:
            assert button is recipe_module.ISLAND_RECIPE_AMOUNT_PLUS
            state.amount = min(maximum, state.amount + n)

    main.appear_then_click = click_max
    main.device.multi_click = adjust
    monkeypatch.setattr(recipe_module.ISLAND_RECIPE_AMOUNT_OCR, 'ocr', lambda image: state.amount)
    return main, state


@pytest.mark.parametrize('initial_amount', [1, 5])
def test_one_batch_does_not_need_max_and_still_verifies_the_amount(monkeypatch, initial_amount):
    main, state = make_recipe(monkeypatch, amount=initial_amount, max_available=False)

    assert main.set_recipe_batch_count(1) is True
    assert state.amount == 1
    assert state.max_clicks == 0
    if initial_amount == 1:
        assert state.adjustments == []
    else:
        assert state.adjustments == [(recipe_module.ISLAND_RECIPE_AMOUNT_MINUS, 4)]


def test_multiple_batches_still_adjust_down_from_max(monkeypatch):
    main, state = make_recipe(monkeypatch)

    assert main.set_recipe_batch_count(3) is True
    assert state.amount == 3
    assert state.max_clicks == 1
    assert state.adjustments == [(recipe_module.ISLAND_RECIPE_AMOUNT_MINUS, 5)]


def test_unlimited_batches_still_select_max(monkeypatch):
    main, state = make_recipe(monkeypatch)

    assert main.set_recipe_batch_count() is True
    assert state.amount == 8
    assert state.max_clicks == 1
    assert state.adjustments == []


def test_insufficient_ingredients_still_reject_an_unavailable_amount(monkeypatch):
    main, state = make_recipe(monkeypatch)
    main.get_recipe_ingredient_counters = lambda: [(8, 12, -4)]

    assert main.set_recipe_batch_count(12) is False
    assert state.max_clicks == 1
    assert state.adjustments == []


def test_failed_single_batch_adjustment_still_returns_false(monkeypatch):
    main, state = make_recipe(monkeypatch, amount=5, max_available=False)

    def fail_adjustment(*args, **kwargs):
        raise GameTooManyClickError

    main.device.multi_click = fail_adjustment

    assert main.set_recipe_batch_count(1) is False
    assert state.max_clicks == 0
