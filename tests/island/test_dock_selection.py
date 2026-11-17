"""Production and collection use dock selection before confirming dispatch."""

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
    main._dock_sorts = []
    main.island_dock_sort_method_dsc_set = lambda enable: main._dock_sorts.append(enable)
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


def character(identity, *, emotion=100, emotion_limit=150, status='free', grade='A'):
    return Character(identity=identity, emotion=emotion, emotion_limit=emotion_limit,
                     status=status, grade=grade, button=object())


def install_dock_pages(main, events, passes, completed=True):
    searches = []
    current_buttons = []

    def search(handle_page, **kwargs):
        pages = passes[len(searches)]
        searches.append(kwargs)
        for page in pages:
            current_buttons[:] = [worker.button for worker in page]
            result = handle_page(page)
            if result is not None:
                return result, True
        return None, completed

    def select(button):
        assert button in current_buttons, 'stale dock button'
        events.append(('select', button))
        return True

    main.island_dock_search = search
    main.is_button_selected = lambda *args, **kwargs: False
    main.island_dock_select_one = select
    return searches


def test_default_setting_uses_workerjuu_before_confirming(production):
    main, events, slot, finish = production
    main.island_dock_select_workerjuu = lambda: events.append('workerjuu') or Character(
        identity='Workerjuu', emotion=None, status='free')
    main.dispatch_slot(slot, None)

    assert events == ['workerjuu', 'confirm', ('recipe', slot, float('inf')), 'production']
    assert main.slot_finish_time[slot] == finish


@pytest.mark.parametrize('emotion', [100, 117, 150])
def test_character_mode_excludes_named_waitresses_and_passes_actual_emotion(production, emotion):
    main, events, _, finish = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    prefix = 'IslandBusiness.IslandRestaurant.'
    main.config.values = {
        prefix + 'CafeWaitress1': 'Belfast', prefix + 'CafeWaitress2': 'none',
        prefix + 'BearWaitress1': 'Chang_Feng', prefix + 'BearWaitress2': 'business_grade',
    }
    chosen = character('Friedrich_der_Grosse', emotion=emotion)
    pages = [[
        character('Belfast', emotion_limit=130), character('Chang_Feng'), chosen,
    ]]
    searches = install_dock_pages(main, events, [pages])
    slot = DIC_ISLAND_PRODUCTION_PLACE[901]['slot'][0]

    main.dispatch_slot(slot, None)

    assert events == [('select', chosen.button), 'confirm', ('recipe', slot, emotion), 'production']
    assert main.slot_finish_time[slot] == finish
    assert searches[0]['descending'] is True
    assert len(searches) == 1
    assert main.production_dock is None


def test_dedicated_skill_on_later_page_beats_shared_and_general_workers(production):
    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    chosen = character('Chen_Hai', grade='C')
    searches = install_dock_pages(main, events, [[
        [character('Royal_Fortune'), character('Explorer')],
        [chosen, character('Saratoga')],
        [character('Le_Malin')],
    ]])

    main.dispatch_slot(slot, None)

    assert events == [('select', chosen.button), 'confirm', ('recipe', slot, 100), 'production']
    assert len(searches) == 1
    assert main.production_dock is None


@pytest.mark.parametrize('place_id,earlier,identity', [
    (602, 'Laffey', 'Chang_Feng'),
    (705, 'Agir', 'Laffey'),
])
def test_first_available_worker_in_highest_pool_stops_discovery(production, place_id, earlier, identity):
    main, events, _, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    chosen = character(identity)
    searches = install_dock_pages(main, events, [[
        [character(earlier), chosen], [character('Royal_Fortune')],
    ]])
    slot = DIC_ISLAND_PRODUCTION_PLACE[place_id]['slot'][0]

    main.dispatch_slot(slot, None)

    assert events == [('select', chosen.button), 'confirm', ('recipe', slot, 100), 'production']
    assert len(searches) == 1
    assert main.production_dock is None


@pytest.mark.parametrize('emotion_limit', [100, 130, 149])
def test_business_a_can_work_below_full_stamina_cap(production, emotion_limit):
    main, events, _, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    chosen = character('Unicorn', emotion_limit=emotion_limit)
    searches = install_dock_pages(main, events, [[[
        character('Fei_Yuen'),
        character('Unicorn', emotion=99, emotion_limit=emotion_limit),
        character('Fei_Yuen', emotion_limit=130, status='occupied'),
        character('New_Jersey'), chosen,
    ]]])
    slot = DIC_ISLAND_PRODUCTION_PLACE[401]['slot'][0]

    main.dispatch_slot(slot, None)

    assert events == [('select', chosen.button), 'confirm', ('recipe', slot, 100), 'production']
    assert len(searches) == 1


@pytest.mark.parametrize('place_id', [101, 501, 502])
def test_discovery_selects_shared_workers_before_general_fallback(production, place_id):
    main, events, _, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    old_shared = character('Hwah_Jah', grade='C')
    chosen = character('Hwah_Jah', grade='C')
    searches = install_dock_pages(main, events, [
        [[character('Laffey')], [old_shared, character('Explorer')]],
        [[character('Laffey')], [chosen, character('Explorer')]],
    ])
    slot = DIC_ISLAND_PRODUCTION_PLACE[place_id]['slot'][0]

    main.dispatch_slot(slot, None)

    assert events == [('select', chosen.button), 'confirm', ('recipe', slot, 100), 'production']
    assert [search['descending'] for search in searches] == [True, False]
    assert [search.get('reverse', False) for search in searches] == [False, True]
    assert ('select', old_shared.button) not in events


@pytest.mark.parametrize('identity,emotion_limit', [
    ('Laffey', 150), ('Royal_Fortune', 150), ('Le_Malin', 130),
])
def test_general_fallback_accepts_unrestricted_workers_in_native_order(production, identity, emotion_limit):
    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    chosen = character(identity, emotion_limit=emotion_limit, grade='C')
    others = [character('Yat_Sen'), character('Prinz_Eugen', emotion_limit=130)]
    pages = [[character(identity, emotion_limit=emotion_limit, grade='C'), *others]]
    searches = install_dock_pages(main, events, [pages, [[chosen, *others]]])

    main.dispatch_slot(slot, None)

    assert events == [('select', chosen.button), 'confirm', ('recipe', slot, 100), 'production']
    assert [search['descending'] for search in searches] == [True, False]
    assert [search.get('reverse', False) for search in searches] == [False, True]


@pytest.mark.parametrize('place_id,specialists,fallback,pass_count', [
    (604, [('Agir', 150), ('Explorer', 150)], 'Laffey', 2),
    (706, [('Yat_Sen', 149)], 'Royal_Fortune', 2),
    (601, [('Nagato', 150)], 'Laffey', 2),
    (705, [('Agir', 150), ('Explorer', 150)], None, 1),
])
def test_outside_specialists_are_reserved_for_their_own_places(
        production, place_id, specialists, fallback, pass_count):
    main, events, _, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    workers = [character(identity, emotion_limit=cap) for identity, cap in specialists]
    chosen = character(fallback) if fallback else None
    if chosen:
        workers.append(chosen)
    searches = install_dock_pages(main, events, [[workers]] * pass_count)
    main.island_dock_select_workerjuu = lambda **kwargs: events.append('workerjuu') or Character(
        identity='Workerjuu', emotion=None, status='free')
    slot = DIC_ISLAND_PRODUCTION_PLACE[place_id]['slot'][0]

    main.dispatch_slot(slot, None)

    selection = ('select', chosen.button) if chosen else 'workerjuu'
    emotion = 100 if chosen else float('inf')
    assert events == [selection, 'confirm', ('recipe', slot, emotion), 'production']
    assert len(searches) == pass_count


@pytest.mark.parametrize('emotion_limit', [150, None])
def test_reserved_or_unreadable_business_a_falls_back_to_workerjuu(production, emotion_limit):
    main, events, _, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    pages = [[character('Yat_Sen', emotion_limit=emotion_limit)]]
    searches = install_dock_pages(main, events, [pages])
    main.island_dock_select_workerjuu = lambda **kwargs: events.append('workerjuu') or Character(
        identity='Workerjuu', emotion=None, status='free')
    slot = DIC_ISLAND_PRODUCTION_PLACE[502]['slot'][0]

    main.dispatch_slot(slot, None)

    assert events == ['workerjuu', 'confirm', ('recipe', slot, float('inf')), 'production']
    assert len(searches) == 1


def test_reserved_business_specialist_does_not_block_shared_worker(production):
    main, events, _, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    chosen = character('Oceana')
    pages = [[character('Unicorn'), chosen]]
    searches = install_dock_pages(main, events, [pages, pages])
    slot = DIC_ISLAND_PRODUCTION_PLACE[401]['slot'][0]

    main.dispatch_slot(slot, None)

    assert events == [('select', chosen.button), 'confirm', ('recipe', slot, 100), 'production']
    assert len(searches) == 2


@pytest.mark.parametrize('named', [False, True])
def test_restaurant_specialist_is_usable_unless_reserved_by_name(production, named):
    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    prefix = 'IslandBusiness.IslandRestaurant.'
    main.config.values = {
        prefix + 'KoiWaitress1': 'business_grade',
        prefix + 'EateryWaitress1': 'Prinz_Eugen' if named else 'none',
    }
    prinz = character('Prinz_Eugen')
    other = character('Royal_Fortune')
    pages = [[prinz, other]]
    install_dock_pages(main, events, [pages, pages])

    main.dispatch_slot(slot, None)

    chosen = other if named else prinz
    assert events == [('select', chosen.button), 'confirm', ('recipe', slot, 100), 'production']


def test_incomplete_skill_search_does_not_choose_lower_priority_worker(production):
    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    searches = install_dock_pages(main, events, [[[character('Royal_Fortune')]]], completed=False)
    main.island_dock_select_workerjuu = lambda **kwargs: events.append('workerjuu') or Character(
        identity='Workerjuu', emotion=None, status='free')

    main.dispatch_slot(slot, None)

    assert events == ['workerjuu', 'confirm', ('recipe', slot, float('inf')), 'production']
    assert len(searches) == 1
    assert main.production_dock is None


def test_exhausted_place_roster_skips_scanning_later_slots(production):
    main, events, _, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    pages = [[character('Agir', emotion=86), character('Laffey', emotion=99)]]
    searches = install_dock_pages(main, events, [pages])
    slots = DIC_ISLAND_PRODUCTION_PLACE[201]['slot'][:2]

    def workerjuu(descending=False):
        assert descending is None
        events.append('workerjuu')
        return Character(identity='Workerjuu', emotion=None, status='free')

    main.island_dock_select_workerjuu = workerjuu
    for slot in slots:
        main.dispatch_slot(slot, None)

    assert len(searches) == 1
    assert main._dock_sorts == [False]
    assert events.count('workerjuu') == 2
    assert all(('recipe', slot, float('inf')) in events for slot in slots)


def test_place_roster_reuses_efficiency_order_and_marks_dispatched_workers_occupied(production):
    main, events, _, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    hwah_jah, explorer = character('Hwah_Jah'), character('Explorer')
    searches = install_dock_pages(main, events, [
        [[character('Hwah_Jah'), character('Explorer')], [character('Laffey')]],
        [[character('Explorer'), hwah_jah]],
        [[character('Hwah_Jah', status='occupied'), explorer]],
    ])
    slots = DIC_ISLAND_PRODUCTION_PLACE[101]['slot'][:2]
    main.slot_grids = {101: SimpleNamespace(buttons=[object(), object()])}
    main.is_slot_empty = lambda button: True
    # An earlier dispatch's roster must be discarded at entry to a new place dispatch.
    main.production_dock = {'Old': character('Old')}

    main.dispatch_place(101)

    assert [search['descending'] for search in searches] == [True, False, True]
    assert [search.get('reverse', False) for search in searches] == [False, True, False]
    assert [event for event in events if isinstance(event, tuple) and event[0] == 'select'] == [
        ('select', hwah_jah.button), ('select', explorer.button),
    ]
    assert all(('recipe', slot, 100) in events for slot in slots)
    assert [(worker.identity, worker.status) for worker in main.production_dock.values()] == [
        ('Hwah_Jah', 'occupied'), ('Explorer', 'occupied'), ('Laffey', 'free'),
    ]
    assert all(worker.button is None for worker in main.production_dock.values())


@pytest.mark.parametrize('failure', ['missing', 'occupied', 'click'])
def test_live_target_failure_invalidates_roster_without_more_searches(production, failure):
    main, events, _, _ = production
    main.production_dock = {
        'Chen_Hai': Character(identity='Chen_Hai', emotion=100, emotion_limit=150, status='free'),
    }
    chosen = character('Chen_Hai', status='occupied' if failure == 'occupied' else 'free')
    target_page = [character('Laffey')] if failure == 'missing' else [chosen]
    searches = install_dock_pages(main, events, [[target_page]])
    if failure == 'click':
        main.island_dock_select_one = lambda button: False

    assert main.select_production_character(101) is None
    assert len(searches) == 1
    assert main.production_dock is None


def test_failed_recipe_keeps_worker_in_place_roster(production, monkeypatch):
    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    chosen = character('Explorer')
    install_dock_pages(main, events, [[[character('Explorer')]], [[chosen]]])
    monkeypatch.setattr(IslandRecipe, 'run', lambda self, **kwargs: None)
    main.ui_back = lambda **kwargs: None
    main.is_enter_window_shown = lambda: False

    assert main.dispatch_slot(slot, None) is False
    assert list(main.production_dock) == ['Explorer']
    assert main.production_dock['Explorer'].status == 'free'
    assert main.slot_finish_time == {}


def test_failed_human_search_does_not_suppress_later_places(production):
    main, events, slot, finish = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    other_slot = DIC_ISLAND_PRODUCTION_PLACE[706]['slot'][0]
    searches = install_dock_pages(main, events, [
        [[character('Hood')]], [[character('Tashkent')]],
    ])
    main.island_dock_select_workerjuu = lambda **kwargs: events.append('workerjuu') or Character(
        identity='Workerjuu', emotion=None, status='free')
    main.slot_grids = {
        place: SimpleNamespace(buttons=[object()]) for place in (101, 706)
    }
    main.is_slot_empty = lambda button: True

    main.dispatch_place(101)
    main.dispatch_place(706)

    assert len(searches) == 2
    assert events.count('workerjuu') == 1
    assert ('recipe', other_slot, 100) in events
    assert main.slot_finish_time == {slot: finish, other_slot: finish}


def test_ingredient_restart_retries_human_workers(production, monkeypatch):
    main, events, slot, finish = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    workers = iter((None, character('Chen_Hai')))

    def select(place_id):
        assert main.production_dock is None
        main.production_dock = {'Earlier': character('Earlier')}
        events.append('character')
        return next(workers)

    main.select_production_character = select
    main.island_dock_select_workerjuu = lambda **kwargs: events.append('workerjuu') or Character(
        identity='Workerjuu', emotion=None, status='free')
    grids = {101: SimpleNamespace(buttons=[object()])}
    monkeypatch.setattr(IslandProduction, 'slot_grids', property(lambda self: grids))
    main.is_slot_empty = lambda button: True
    main.ensure_top_page = lambda: None
    main.next_page = lambda: False
    recipe_calls = []

    def recipe(self, slot_id, emotion):
        recipe_calls.append(emotion)
        if len(recipe_calls) == 1:
            raise IslandProductionRestart(item_id=3004)
        return finish

    monkeypatch.setattr(IslandRecipe, 'run', recipe)
    main.dispatch_all(check_all_empty_slots=True)

    assert recipe_calls == [float('inf'), 100]
    assert events.count('character') == 2
    assert events.count('workerjuu') == 1


def test_failed_workerjuu_selection_cancels_without_confirming(production):
    main, events, slot, _ = production
    main.island_dock_select_workerjuu = lambda: events.append('workerjuu') or None

    assert main.dispatch_slot(slot, None) is False
    assert events == ['workerjuu', 'cancel']
    assert main.slot_finish_time == {}


def test_character_mode_cancels_when_character_and_workerjuu_selection_fail(production):
    main, events, slot, _ = production
    main.config.IslandProduction_UseWorkerjuuByDefault = False
    main.select_production_character = lambda place_id: events.append('character') or None
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

    def select(predicate, **kwargs):
        assert predicate(character(None, emotion=80, emotion_limit=None))
        assert not predicate(character(None, emotion=79, emotion_limit=None))
        assert not predicate(character(None, emotion=100, status='occupied'))
        events.append(('select', kwargs))
        return None

    main.island_dock_select_character = select

    assert main.collect_execute() is False
    assert events == [
        ('select', {'descending': False, 'disabled': ('identity', 'emotion_limit', 'grade')}),
        'cancel',
    ]
