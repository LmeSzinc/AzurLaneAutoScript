"""Production and collection use dock selection before confirming dispatch."""

from collections import deque
from datetime import datetime
from types import SimpleNamespace

import pytest

from module.island.collect import IslandCollect
from module.island.production import IslandProduction
from module.island_handler.recipe import IslandProductionRestart, IslandRecipe
from module.island_handler.dock_scanner import Character
from module.island.data import DIC_ISLAND_PRODUCTION_PLACE


class ProductionConfig:
    def __init__(self):
        self.IslandProduction_UseWorkerjuuByDefault = True
        self.values = {}

    def cross_get(self, key, default=None):
        return self.values.get(key, default)


@pytest.fixture
def production(monkeypatch):
    main = object.__new__(IslandProduction)
    events = []
    finish = datetime(2026, 10, 29, 12)
    slot = DIC_ISLAND_PRODUCTION_PLACE[101]['slot'][0]
    main.config = ProductionConfig()
    main.device = SimpleNamespace(click_record_remove=lambda name: None)
    main.slot_finish_time = {}
    main.loop = lambda **kwargs: iter((None,))
    main.is_in_island_dock = lambda: True
    main.is_in_recipe_menu = lambda: True
    main.island_dock_select_confirm = lambda check: events.append('confirm')
    main.island_dock_quit = lambda: events.append('cancel')
    main.ensure_island_production_page = lambda: events.append('production')

    def recipe(self, slot_id, emotion):
        events.append(('recipe', slot_id, emotion))
        return finish

    monkeypatch.setattr(IslandRecipe, 'run', recipe)
    return main, events, slot, finish


def test_default_setting_uses_workerjuu_before_confirming(production):
    main, events, slot, finish = production
    main.island_dock_select_workerjuu = lambda: events.append('workerjuu') or Character(
        identity='Workerjuu', emotion=None, status='free')
    main.dispatch_slot(slot, None)

    assert events == ['workerjuu', 'confirm', ('recipe', slot, float('inf')), 'production']
    assert main.slot_finish_time[slot] == finish


@pytest.mark.parametrize('emotion', [100, 117, 130])
def test_character_mode_excludes_named_waitresses_and_passes_actual_emotion(production, emotion):
    main, events, slot, finish = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    prefix = 'IslandBusiness.IslandRestaurant.'
    main.config.values = {
        prefix + 'KoiWaitress1': 'Chao_Ho', prefix + 'KoiWaitress2': 'any',
        prefix + 'BearWaitress1': 'Cheshire', prefix + 'BearWaitress2': 'Chang_Feng',
        prefix + 'EateryWaitress1': 'Prinz_Eugen', prefix + 'EateryWaitress2': 'none',
        prefix + 'GrillWaitress1': 'August_von_Parseval', prefix + 'GrillWaitress2': 'Chang_Feng',
        prefix + 'CafeWaitress1': 'Belfast', prefix + 'CafeWaitress2': 'Cheshire',
    }

    def select(**kwargs):
        events.append(('select', kwargs))
        return Character(identity='Yat_Sen', emotion=emotion, emotion_limit=130, status='free')

    main.island_dock_select_character = select
    main.dispatch_slot(slot, None)

    assert events == [
        ('select', {'emotion': (100, 150), 'emotion_limit': (100, 149), 'descending': False,
                    'blacklist': {'Chao_Ho', 'Cheshire', 'Chang_Feng', 'Prinz_Eugen',
                                  'August_von_Parseval', 'Belfast'}}),
        'confirm', ('recipe', slot, emotion), 'production',
    ]
    assert main.slot_finish_time[slot] == finish


@pytest.mark.parametrize('emotion_limit', [100, 130, 149])
def test_character_mode_selects_free_unreserved_character_below_150_emotion_limit(production, emotion_limit):
    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    main.config.values['IslandBusiness.IslandRestaurant.KoiWaitress1'] = 'Chao_Ho'
    candidates = [
        Character(identity='Chao_Ho', emotion=120, emotion_limit=130, status='free', button=object()),
        Character(identity='Workerjuu', emotion=999, emotion_limit=999, status='free', button=object()),
        Character(identity='Yat_Sen', emotion=99, emotion_limit=130, status='free', button=object()),
        Character(identity='Chen_Hai', emotion=100, emotion_limit=130, status='occupied', button=object()),
        Character(identity='New_Jersey', emotion=120, emotion_limit=150, status='free', button=object()),
        Character(identity='Helena', emotion=100, emotion_limit=None, status='free', button=object()),
        Character(identity='Fei_Yuen', emotion=100, emotion_limit=emotion_limit, status='free', button=object()),
    ]
    searches = []

    def search(handle_page, **kwargs):
        searches.append(kwargs)
        return handle_page(candidates), True

    main.island_dock_search = search
    main.is_button_selected = lambda *args, **kwargs: False
    main.island_dock_select_one = lambda button: events.append(('select', button)) or True
    main.dispatch_slot(slot, None)

    assert events == [('select', candidates[-1].button), 'confirm', ('recipe', slot, 100), 'production']
    assert len(searches) == 1
    assert searches[0]['descending'] is False
    assert 'identity' not in searches[0]['disabled']
    assert 'emotion_limit' not in searches[0]['disabled']


def test_no_usable_character_falls_back_to_workerjuu(production):
    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    main.island_dock_select_character = lambda **kwargs: events.append('character') or None
    main.island_dock_select_workerjuu = lambda **kwargs: events.append('workerjuu') or Character(
        identity='Workerjuu', emotion=None, status='free')

    main.dispatch_slot(slot, None)

    assert events == ['character', 'workerjuu', 'confirm', ('recipe', slot, float('inf')), 'production']


def test_failed_human_search_clears_down_swipes_before_workerjuu_fallback(production):
    from module.device.device import Device

    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    down = 'ISLAND_DOCK_NEXT_PAGE_SWIPE'
    sorting = 'ISLAND_DOCK_SORTING_CLICK'
    main.device = object.__new__(Device)
    main.device.click_record = deque([down] * 6 + [sorting] * 5 + ['OTHER_ACTION'], maxlen=15)
    main.island_dock_select_character = lambda **kwargs: events.append('character') or None

    def workerjuu(descending=False):
        assert descending is True
        main.device.click_record_add(sorting)
        main.device.click_record_check()
        events.append('workerjuu')
        return Character(identity='Workerjuu', emotion=None, status='free')

    main.island_dock_select_workerjuu = workerjuu
    main.dispatch_slot(slot, None)

    assert events == ['character', 'workerjuu', 'confirm', ('recipe', slot, float('inf')), 'production']
    assert list(main.device.click_record) == [sorting] * 5 + ['OTHER_ACTION', sorting]


def test_failed_human_search_is_shared_across_production_places(production):
    main, events, slot, finish = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    main.island_dock_select_character = lambda **kwargs: events.append('character') or None
    workerjuu_orders = []

    def workerjuu(descending=False):
        workerjuu_orders.append(descending)
        events.append('workerjuu')
        return Character(identity='Workerjuu', emotion=None, status='free')

    main.island_dock_select_workerjuu = workerjuu
    other_slot = DIC_ISLAND_PRODUCTION_PLACE[706]['slot'][0]

    main.dispatch_slot(slot, None)
    main.dispatch_slot(other_slot, None)

    assert events.count('character') == 1
    assert events.count('workerjuu') == 2
    assert workerjuu_orders == [True, False]
    assert main.slot_finish_time == {slot: finish, other_slot: finish}
    assert main.human_workers_available is False


def test_next_dispatch_pass_retries_human_workers(production):
    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    workers = iter((None, Character(identity='Yat_Sen', emotion=100, emotion_limit=130, status='free')))

    def select(**kwargs):
        events.append('character')
        return next(workers)

    main.island_dock_select_character = select
    main.island_dock_select_workerjuu = lambda **kwargs: events.append('workerjuu') or Character(
        identity='Workerjuu', emotion=None, status='free')
    main.slot_grids = {101: SimpleNamespace(buttons=[object()])}
    main.is_slot_empty = lambda button: True
    main.ensure_top_page = lambda: None
    main.next_page = lambda: False

    main.dispatch_all(check_all_empty_slots=True)
    assert main.human_workers_available is False
    main.dispatch_all(check_all_empty_slots=True)

    assert events.count('character') == 2
    assert events.count('workerjuu') == 1
    assert events[-2] == ('recipe', slot, 100)
    assert main.human_workers_available is True


def test_ingredient_restart_does_not_repeat_failed_human_search(production, monkeypatch):
    main, events, slot, finish = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    main.island_dock_select_character = lambda **kwargs: events.append('character') or None
    main.island_dock_select_workerjuu = lambda **kwargs: events.append('workerjuu') or Character(
        identity='Workerjuu', emotion=None, status='free')
    grids = {101: SimpleNamespace(buttons=[object()])}
    monkeypatch.setattr(IslandProduction, 'slot_grids', property(lambda self: grids))
    main.is_slot_empty = lambda button: True
    main.ensure_top_page = lambda: None
    main.next_page = lambda: False
    recipe_calls = []

    def recipe(self, slot_id, emotion):
        recipe_calls.append(slot_id)
        if len(recipe_calls) == 1:
            raise IslandProductionRestart(item_id=3004)
        return finish

    monkeypatch.setattr(IslandRecipe, 'run', recipe)
    main.dispatch_all(check_all_empty_slots=True)

    assert recipe_calls == [slot, slot]
    assert events.count('character') == 1
    assert events.count('workerjuu') == 2
    assert main.human_workers_available is False


@pytest.mark.parametrize('emotion_limit', [150, None])
def test_mature_or_unreadable_emotion_limit_falls_back_to_workerjuu(production, emotion_limit):
    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    candidate = Character(identity='Yat_Sen', emotion=100, emotion_limit=emotion_limit,
                          status='free', button=object())
    main.island_dock_search = lambda handle_page, **kwargs: (handle_page([candidate]), True)
    main.island_dock_select_one = lambda button: pytest.fail('Selected an ineligible production worker')
    main.island_dock_select_workerjuu = lambda **kwargs: events.append('workerjuu') or Character(
        identity='Workerjuu', emotion=None, status='free')

    main.dispatch_slot(slot, None)

    assert events == ['workerjuu', 'confirm', ('recipe', slot, float('inf')), 'production']


def test_character_mode_passes_emotion_without_identity_recognition(production):
    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    candidate = Character(identity=None, emotion=117, emotion_limit=130, status='free', button=object())
    searches = []

    def search(handle_page, **kwargs):
        searches.append(kwargs)
        return handle_page([candidate]), True

    main.island_dock_search = search
    main.is_button_selected = lambda *args, **kwargs: False
    main.island_dock_select_one = lambda button: events.append(('select', button)) or True
    main.dispatch_slot(slot, None)

    assert events == [('select', candidate.button), 'confirm', ('recipe', slot, 117), 'production']
    assert 'identity' in searches[0]['disabled']
    assert 'emotion_limit' not in searches[0]['disabled']


def test_failed_workerjuu_selection_cancels_without_confirming(production):
    main, events, slot, _ = production
    main.island_dock_select_workerjuu = lambda: events.append('workerjuu') or None

    assert main.dispatch_slot(slot, None) is False
    assert events == ['workerjuu', 'cancel']
    assert main.slot_finish_time == {}


def test_character_mode_cancels_when_character_and_workerjuu_selection_fail(production):
    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    main.island_dock_select_character = lambda **kwargs: events.append('character') or None
    main.island_dock_select_workerjuu = lambda **kwargs: events.append('workerjuu') or None

    assert main.dispatch_slot(slot, None) is False
    assert events == ['character', 'workerjuu', 'cancel']
    assert main.slot_finish_time == {}


def test_dispatch_place_does_not_override_configured_default_worker(production):
    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    button = object()
    main.slot_grids = {101: SimpleNamespace(buttons=[button])}
    main.is_slot_empty = lambda slot_button: True
    main.dispatch_slot = lambda slot_id, slot_button: events.append((slot_id, slot_button))

    main.dispatch_place(101)

    assert events == [(slot, button)]


def test_collect_keeps_emotion_filter_and_cancels_failed_selection():
    main = object.__new__(IslandCollect)
    events = []
    main.loop = lambda **kwargs: iter((None,))
    main.is_in_island_dock = lambda: True
    main.island_dock_quit = lambda: events.append('cancel')

    def select(**kwargs):
        events.append(('select', kwargs))
        return None

    main.island_dock_select_character = select

    assert main.collect_execute() is False
    assert events == [
        ('select', {'emotion': (80, 150), 'descending': False,
                    'disabled': ('emotion_limit',)}),
        'cancel',
    ]
