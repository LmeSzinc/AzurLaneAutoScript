"""Production and collection use dock selection before confirming dispatch."""

from datetime import datetime

import pytest

from module.island.collect import IslandCollect
from module.island.production import IslandProduction
from module.island_handler.recipe import IslandRecipe
from module.island.data import DIC_ISLAND_PRODUCTION_PLACE


@pytest.fixture
def production(monkeypatch):
    main = object.__new__(IslandProduction)
    events = []
    finish = datetime(2026, 10, 29, 12)
    slot = DIC_ISLAND_PRODUCTION_PLACE[101]['slot'][0]
    main.slot_finish_time = {}
    main.loop = lambda **kwargs: iter((None,))
    main.is_in_island_dock = lambda: True
    main.is_in_recipe_menu = lambda: True
    main.island_dock_select_confirm = lambda check: events.append('confirm')
    main.island_dock_quit = lambda: events.append('cancel')
    main.ensure_island_production_page = lambda: events.append('production')

    def recipe(self, slot_id):
        events.append(('recipe', slot_id))
        return finish

    monkeypatch.setattr(IslandRecipe, 'run', recipe)
    return main, events, slot, finish


def test_named_worker_uses_filtered_fallback_before_confirming(production):
    main, events, slot, finish = production

    def select(**kwargs):
        events.append(('select', kwargs))
        return True

    main.island_dock_select_character = select
    main.dispatch_slot(slot, None, worker='Yat_Sen')

    assert events == [
        ('select', {'identity': 'Yat_Sen', 'fallback': True}),
        'confirm', ('recipe', slot), 'production',
    ]
    assert main.slot_finish_time[slot] == finish


def test_no_usable_character_falls_back_to_manjuu(production):
    main, events, slot, _ = production
    main.island_dock_select_character = lambda **kwargs: events.append('character') or False
    main.island_dock_select_manjuu = lambda: events.append('manjuu') or True

    main.dispatch_slot(slot, None, worker='Yat_Sen')

    assert events == ['character', 'manjuu', 'confirm', ('recipe', slot), 'production']


def test_failed_manjuu_selection_cancels_without_confirming(production):
    main, events, slot, _ = production
    main.island_dock_select_manjuu = lambda: events.append('manjuu') or False

    assert main.dispatch_slot(slot, None) is False
    assert events == ['manjuu', 'cancel']
    assert main.slot_finish_time == {}


def test_collect_keeps_emotion_filter_and_cancels_failed_selection():
    main = object.__new__(IslandCollect)
    events = []
    main.loop = lambda **kwargs: iter((None,))
    main.is_in_island_dock = lambda: True
    main.island_dock_quit = lambda: events.append('cancel')

    def select(**kwargs):
        events.append(('select', kwargs))
        return False

    main.island_dock_select_character = select

    assert main.collect_execute() is False
    assert events == [
        ('select', {'emotion': (80, 150), 'descending': False,
                    'disabled': ('emotion_limit',)}),
        'cancel',
    ]
