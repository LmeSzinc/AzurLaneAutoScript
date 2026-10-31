"""Recipe stock scans end only at a recognized list boundary."""
from types import SimpleNamespace

import pytest

from module.base.button import ButtonGrid
import module.island_handler.recipe as recipe_module
from module.island_handler.recipe import IslandRecipe, RECIPE_DELTA, RECIPE_SIZE


def page(recipe_ids, origin=(181, 114)):
    return SimpleNamespace(stocks={recipe_id: recipe_id * 10 for recipe_id in recipe_ids}, origin=origin)


def make_recipe(monkeypatch, pages):
    main = object.__new__(IslandRecipe)
    state = SimpleNamespace(index=0, next_calls=0, scans=[], clears=0, reference=None)

    def clear_clicks():
        state.clears += 1

    def get_grid():
        current = pages[state.index]
        return ButtonGrid(origin=current.origin, delta=RECIPE_DELTA, button_shape=RECIPE_SIZE,
                          grid_shape=(1, len(current.stocks)), name='RECIPE_GRID')

    def update_page():
        current = pages[state.index]
        main.recipe_grid = get_grid()
        main.recipe_ids = list(current.stocks)
        main.device.image = (current.origin, tuple(current.stocks.items()))

    def stocks():
        state.scans.append(state.index)
        return list(pages[state.index].stocks.values())

    def next_page():
        state.next_calls += 1
        state.index = min(state.index + 1, len(pages) - 1)
        update_page()

    def load_color(image):
        state.reference = image

    drag_check = SimpleNamespace(load_color=load_color)
    monkeypatch.setattr(recipe_module, 'ISLAND_RECIPE_DRAG_CHECK', drag_check)
    main.device = SimpleNamespace(click_record_clear=clear_clicks)
    main.loop = lambda **kwargs: range(len(pages) + 3)
    main.appear = lambda button, **kwargs: button is not drag_check or main.device.image == state.reference
    main.get_recipe_grid = get_grid
    main.get_recipe_ids = lambda: list(pages[state.index].stocks)
    main.get_recipe_product_stocks = stocks
    main.next_recipe_page = next_page
    update_page()
    return main, state


def test_stock_scan_reads_the_bottom_page_before_stopping(monkeypatch):
    pages = [page([1, 2, 3]), page([3, 4, 5], (181, 162)), page([5, 6, 7, 8], (181, 71))]
    main, state = make_recipe(monkeypatch, pages)

    assert main.scan_all_recipe_stocks() == {recipe_id: recipe_id * 10 for recipe_id in range(1, 9)}
    assert state.scans == [0, 1, 2]
    assert state.next_calls == 2
    assert state.clears == 1


def test_stock_scan_retries_failed_drags_instead_of_missing_later_recipes(monkeypatch):
    first = page([1, 2, 3])
    main, state = make_recipe(monkeypatch, [first, first, first, page([3, 4, 5, 6], (181, 71))])

    assert main.scan_all_recipe_stocks() == {recipe_id: recipe_id * 10 for recipe_id in range(1, 7)}
    assert state.scans == [0, 1, 2, 3]
    assert state.next_calls == 3


@pytest.mark.parametrize('origin, count', [
    ((181, 114), 3),
    ((181, 162), 3),
    ((181, 70), 4),
    ((181, 72), 4),
    ((180, 71), 4),
    ((181, 71), 3),
])
def test_unchanged_unaligned_grid_does_not_end_the_scan(monkeypatch, origin, count):
    current = page(range(1, count + 1), origin)
    main, state = make_recipe(monkeypatch, [current])

    assert main.scan_all_recipe_stocks() == current.stocks
    assert len(state.scans) == 4
    assert state.next_calls == 4
    assert state.clears == 0


@pytest.mark.parametrize('count', [1, 2])
def test_short_top_list_does_not_need_another_drag(monkeypatch, count):
    current = page(range(1, count + 1))
    main, state = make_recipe(monkeypatch, [current])

    assert main.scan_all_recipe_stocks() == current.stocks
    assert state.scans == [0]
    assert state.next_calls == 0
    assert state.clears == 1


def test_bottom_grid_does_not_need_another_drag(monkeypatch):
    current = page([1, 2, 3, 4], (181, 71))
    main, state = make_recipe(monkeypatch, [current])

    assert main.scan_all_recipe_stocks() == current.stocks
    assert state.scans == [0]
    assert state.next_calls == 0
