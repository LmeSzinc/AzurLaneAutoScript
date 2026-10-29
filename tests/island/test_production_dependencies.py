from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from module.island.data import DIC_ISLAND_PRODUCTION_PLACE
from module.island.collect import IslandCollect
from module.island.order import IslandOrder
from module.island.production import IslandProduction
from module.island.transport import IslandTransport


CHECK_ALL = 'IslandProduction.Storage.Storage.CheckAllEmptySlots'


@pytest.fixture(autouse=True)
def continuous_alas_process(monkeypatch):
    monkeypatch.setattr(IslandProduction, '_first_run', False)


class ProductionConfig:
    def __init__(self, values):
        self.values = dict(values)
        self.writes = []

    def cross_get(self, key, default=None):
        return self.values.get(key, default)

    def cross_set(self, key, value):
        self.values[key] = value
        self.writes.append((key, value))

    def multi_set(self):
        return nullcontext()

    def task_delay(self, **kwargs):
        pass


def make_production(places=(602, 706), claimed=(9207,), config=None):
    main = object.__new__(IslandProduction)
    main.config = ProductionConfig({
        'IslandProduction.IslandProduction.DailyBufferItems': '{2000: 1}',
        **(config or {}),
    })
    main.slot_grids = {
        place: SimpleNamespace(buttons=DIC_ISLAND_PRODUCTION_PLACE[place]['slot'])
        for place in places
    }
    main.claimed_slots = set(claimed)
    main.slot_finish_time = {}
    main.ensure_island_production_page = lambda: None
    main.claim_all_rewards = lambda: setattr(main, 'claimed_slots', set(claimed))
    events = []
    main.ensure_top_page = lambda: events.append('top')
    main.next_page = lambda: False
    main.is_slot_empty = lambda button: events.append(('empty', button)) or True
    main.dispatch_slot = lambda slot_id, slot_button: events.append(('dispatch', slot_id))
    return main, events


def dispatched(events):
    return [event[1] for event in events if event[0] == 'dispatch']


def make_transport(config, monkeypatch, claimed=True):
    import module.island.transport as transport

    main = object.__new__(IslandTransport)
    main.config = config
    state = SimpleNamespace(frame=0, clicks=[])

    def loop(**kwargs):
        for state.frame in range(2):
            yield None

    main.loop = loop
    main.handle_transport_popup = lambda: False
    main.is_in_transport_main = lambda: True
    main.slot_appear = lambda button, slot, **kwargs: claimed and state.frame == 0 and slot == 0
    main.device = SimpleNamespace(click=lambda button: state.clicks.append(button))
    timer = SimpleNamespace(reset=lambda: None, reached=lambda: True)
    timer.start = lambda: timer
    monkeypatch.setattr(transport, 'Timer', lambda *args, **kwargs: timer)
    return main, state


def test_finished_craft_slot_does_not_check_empty_teahouse():
    main, events = make_production()

    main.dispatch_all()

    assert dispatched(events) == [9207, 9208]
    assert ('empty', 9071) not in events
    assert ('empty', 9072) not in events


def test_second_product_retries_its_consumer_and_the_finished_slot():
    main, events = make_production(places=(102, 706), claimed=(9033,))

    main.dispatch_all(check_all_empty_slots=False)

    assert dispatched(events) == [9033, 9207, 9208]
    assert ('empty', 9031) not in events
    assert ('empty', 9032) not in events
    assert ('empty', 9034) not in events


def test_crop_to_feed_retries_each_ranch_recipe_independently():
    main, events = make_production(places=(102,), claimed=(9001,))

    def dispatch(slot_id, slot_button):
        events.append(('dispatch', slot_id))
        main.recipe_id_sequence = []

    main.dispatch_slot = dispatch
    main.dispatch_all(check_all_empty_slots=False)

    assert dispatched(events) == [9031, 9032, 9033, 9034]


@pytest.mark.parametrize(('claimed', 'expected'), [
    ((9207,), [9207, 9208]),
    ((), []),
])
def test_missing_full_check_flag_uses_dependencies(claimed, expected):
    main, events = make_production(claimed=claimed)

    main.run()

    assert dispatched(events) == expected
    assert main.config.cross_get(CHECK_ALL) is False


@pytest.mark.parametrize('claimed', [(9207,), ()])
def test_first_production_pass_checks_every_empty_slot(monkeypatch, claimed):
    monkeypatch.setattr(IslandProduction, '_first_run', True)
    main, events = make_production(claimed=claimed, config={CHECK_ALL: False})

    main.run()

    assert dispatched(events) == [9071, 9072, 9207, 9208]
    assert IslandProduction._first_run is False
    assert main.config.cross_get(CHECK_ALL) is False


def test_next_production_instance_in_same_process_uses_dependencies(monkeypatch):
    monkeypatch.setattr(IslandProduction, '_first_run', True)
    first, first_events = make_production(config={CHECK_ALL: False})
    first.run()
    second, second_events = make_production(config={CHECK_ALL: False})

    second.run()

    assert dispatched(first_events) == [9071, 9072, 9207, 9208]
    assert dispatched(second_events) == [9207, 9208]


def test_interrupted_first_pass_does_not_mark_process_checked(monkeypatch):
    monkeypatch.setattr(IslandProduction, '_first_run', True)
    main, _ = make_production(config={CHECK_ALL: False})

    def fail(slot_id, slot_button):
        raise RuntimeError('interrupted dispatch')

    main.dispatch_slot = fail

    with pytest.raises(RuntimeError, match='interrupted dispatch'):
        main.run()

    assert IslandProduction._first_run is True
    assert main.config.cross_get(CHECK_ALL) is True


def test_explicit_full_check_flag_is_consumed_after_one_run():
    main, events = make_production(config={CHECK_ALL: True})

    main.run()

    assert dispatched(events) == [9071, 9072, 9207, 9208]
    assert main.config.cross_get(CHECK_ALL) is False

    events.clear()
    main.run()

    assert dispatched(events) == [9207, 9208]


def test_transport_claim_allows_next_run_to_check_unrelated_empty_slots(monkeypatch):
    main, events = make_production(config={CHECK_ALL: False})
    transport, _ = make_transport(main.config, monkeypatch)

    assert transport.transport_claim_rewards() is True
    assert main.config.writes == [(CHECK_ALL, True)]

    main.run()

    assert dispatched(events) == [9071, 9072, 9207, 9208]
    assert main.config.cross_get(CHECK_ALL) is False


@pytest.mark.parametrize('claimed', [True, False])
@pytest.mark.parametrize('initial', [{}, {CHECK_ALL: False}])
def test_transport_claims_request_full_check_without_reward_popup(monkeypatch, claimed, initial):
    main, state = make_transport(ProductionConfig(initial), monkeypatch, claimed)

    assert main.transport_claim_rewards() is True
    assert len(state.clicks) == int(claimed)
    assert main.config.cross_get(CHECK_ALL, default=False) is claimed


@pytest.mark.parametrize('success', [True, False])
def test_collect_unlocks_next_production_check_after_success(success):
    main, events = make_production(config={CHECK_ALL: False})
    collect = object.__new__(IslandCollect)
    collect.config = main.config
    collect.ui_ensure = lambda *args, **kwargs: None
    collect.island_manage_side_navbar_ensure = lambda **kwargs: None
    collect.collect_available = lambda: True
    collect.collect_execute = lambda: success

    collect.run()
    assert main.config.cross_get(CHECK_ALL) is success
    main.run()

    assert dispatched(events) == ([9071, 9072, 9207, 9208] if success else [9207, 9208])


def test_no_completion_or_external_reward_does_not_retry_empty_slots():
    main, events = make_production(claimed=())

    main.dispatch_all()

    assert events == []


@pytest.mark.parametrize('check_all', [True, False])
def test_failed_dispatch_preserves_pending_full_check(check_all):
    main, _ = make_production(config={CHECK_ALL: check_all})

    def fail(slot_id, slot_button):
        raise RuntimeError('interrupted dispatch')

    main.dispatch_slot = fail

    with pytest.raises(RuntimeError, match='interrupted dispatch'):
        main.run()

    assert main.config.cross_get(CHECK_ALL) is True


def test_transport_submission_does_not_request_full_check():
    main = object.__new__(IslandTransport)
    main.config = ProductionConfig({CHECK_ALL: False})
    main.transport_submit = lambda slot: slot == 0

    assert main.transport_execute_plan(([], [0, 1])) == (True, False)
    assert main.config.cross_get(CHECK_ALL) is False


def test_parking_transport_commissions_does_not_request_full_check():
    main = object.__new__(IslandTransport)
    main.config = ProductionConfig({CHECK_ALL: False})

    assert main.transport_execute_plan(([], [0]), submit=False) == (False, True)
    assert main.config.cross_get(CHECK_ALL) is False


@pytest.mark.parametrize('submitted', [True, False])
def test_order_submission_does_not_request_full_check(submitted):
    main = object.__new__(IslandOrder)
    main.config = ProductionConfig({CHECK_ALL: False})
    main.handle_island_additional = lambda: False
    main.handle_info_bar = lambda: None
    main.click_order = lambda *args, **kwargs: None
    main.appear = lambda *args, **kwargs: False
    main.scan_current_order_requirements = lambda: {}
    main.is_order_satisfied = lambda *args, **kwargs: True
    main.submit_order = lambda **kwargs: submitted

    assert main.execute_order(object(), is_urgent=True) is submitted
    assert main.config.cross_get(CHECK_ALL) is False
