"""Transport refresh policy, preservation, cooldown and action sequencing."""

from copy import deepcopy
from datetime import datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

import module.island.transport as transport
from module.island.transport import IslandTransport, ScannedCommission, TransportRewards
from module.island_handler.milp import Bounds, LinearConstraint

NOW = datetime(2026, 10, 24, 3)
ORE = 2703
CARROT = 2004


class FrozenDatetime(datetime):
    @classmethod
    def now(cls):
        return NOW


class Config:
    def __init__(self):
        self.storage = {}
        self.delays = []
        self.calls = []

    def cross_get(self, key, default=None):
        return self.storage.get(key, default)

    def cross_set(self, key, value):
        self.storage[key] = value

    def task_delay(self, **kwargs):
        self.delays.append(kwargs)

    def task_call(self, name, force_call):
        self.calls.append((name, force_call))


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    monkeypatch.setattr(transport, 'datetime', FrozenDatetime)


@pytest.fixture
def outside_item_problem(monkeypatch):
    """Fixed production, so transport items have their explicit PT values."""
    problem = {
        'c': np.array([0.]),
        'bounds': Bounds([0.], [0.]),
        'constraints': LinearConstraint(np.array([[1.]]), [0.], [0.]),
        'constraint_labels': [('fixture', 0)],
    }
    monkeypatch.setattr(transport, 'create_production_problem', lambda config: problem)


def job(name, required=ORE, need=10, reward=20):
    scanned = ScannedCommission(name)
    scanned.submissions = [(required, need)]
    scanned.rewards = TransportRewards({ORE: reward})
    return scanned


def scenario(primaries, listed=(), stock=None, remaining=(1, 1, 1), running=(), fresh_list=()):
    """A stateful game adapter; real policy, optimizer and plan verification stay in use."""
    board = SimpleNamespace(
        primary=list(primaries), listed={index + 1: value for index, value in enumerate(listed)},
        stock=dict(stock or {}), remaining=list(remaining), running=set(running),
        events=[], refresh_at=NOW, refreshes=0, fail_swap=False, fail_submit=None,
    )
    main = object.__new__(IslandTransport)
    main.config = Config()
    main.hard_floor = {}
    main.reserve = {}
    main.server_support_island_transport = lambda: True
    main.ui_ensure = lambda page: None
    main.transport_claim_rewards = lambda: board.events.append(('claim',)) or True
    main.needs_fish_meat = lambda commissions, max_commissions: False

    def read(scanned, slot=None, index=None):
        result = deepcopy(scanned)
        result.slot, result.index = slot, index
        result.stock = {item: board.stock.get(item, 0) for item, _ in result.submissions}
        if slot is not None:
            result.name = f'P{slot + 1}'
            result.remaining = board.remaining[slot]
        return result

    def scan_slots(rewards=True):
        board.events.append(('scan_primary',))
        states, slots = [], {}
        for slot in range(3):
            if slot in board.running:
                states.append('running')
                continue
            if board.primary[slot] is None:
                empty = ScannedCommission(f'P{slot + 1}', slot=slot)
                empty.empty, empty.remaining = True, board.remaining[slot]
                slots[slot] = empty
                states.append('empty')
            else:
                slots[slot] = read(board.primary[slot], slot=slot)
                states.append('ready' if board.remaining[slot] else 'exhausted')
        return states, slots

    def scan_list():
        board.events.append(('scan_list',))
        main.transport_refresh_time = board.refresh_at
        return {index: read(value, index=index) for index, value in board.listed.items()}

    def swap(slot, sub):
        board.events.append(('swap', slot, sub.name))
        if board.fail_swap:
            return False
        assert slot not in board.running
        board.primary[slot] = board.listed.pop(sub.index)
        return True

    def submit(slot):
        board.events.append(('submit', slot))
        if board.fail_submit == slot:
            return False
        assert board.remaining[slot] > 0
        for item, need in board.primary[slot].submissions:
            assert board.stock.get(item, 0) >= need
            board.stock[item] -= need
        board.running.add(slot)
        board.remaining[slot] -= 1
        return True

    def refresh():
        board.events.append(('refresh',))
        board.refreshes += 1
        board.listed = {index + 1: value for index, value in enumerate(fresh_list)}
        for slot in range(3):
            if board.primary[slot] is None:
                board.primary[slot] = job('refilled', reward=1)
        board.refresh_at = NOW + transport.REFRESH_COOLDOWN
        main.transport_save_refresh_time(board.refresh_at)
        return True

    main.transport_scan_slots = scan_slots
    main.transport_scan_list = scan_list
    main.transport_swap = swap
    main.transport_submit = submit
    main.transport_refresh_list = refresh
    main.transport_next_run_time = lambda: NOW + timedelta(hours=1) if board.running else None
    return main, board


def actions(board):
    return [event for event in board.events if event[0] in ('swap', 'submit', 'refresh')]


def test_submit_then_refresh_and_rescan(outside_item_problem):
    main, board = scenario(
        [job('good'), job('bad', reward=1), job('bad', reward=1)], stock={ORE: 100},
        fresh_list=[job('new01'), job('new02')],
    )
    main.run()
    assert actions(board) == [
        ('submit', 0), ('refresh',), ('swap', 1, 'new01'), ('swap', 2, 'new02'),
        ('submit', 1), ('submit', 2),
    ]
    assert board.running == {0, 1, 2}
    assert board.refreshes == 1
    assert main.config.calls == [('IslandOrder', False)]
    assert main.next_run_time == NOW + timedelta(hours=1)


def test_preserve_stock_blocked_list_job_in_empty_spent_slot(outside_item_problem):
    blocked = job('blocked', reward=100)
    main, board = scenario(
        [job('bad', reward=1), None, job('running')], [blocked], stock={CARROT: 10},
        remaining=(1, 0, 0), running=(2,), fresh_list=[job('stocked', required=CARROT, need=1)],
    )
    main.run()
    assert actions(board) == [
        ('swap', 1, 'blocked'), ('refresh',), ('swap', 0, 'stocked'), ('submit', 0),
    ]
    assert board.primary[1].name == 'blocked'
    assert board.remaining[1] == 0
    assert 1 not in board.running


def test_preserve_better_primary_and_fill_empty_space(outside_item_problem):
    main, board = scenario(
        [job('best', reward=100), None, job('running')], [job('lesser', reward=30)],
        remaining=(1, 0, 0), running=(2,),
    )
    main.run()
    assert actions(board) == [('swap', 1, 'lesser'), ('refresh',)]
    assert board.primary[0].name == 'best'
    assert board.primary[1].name == 'lesser'
    assert board.refreshes == 1
    # Still blocked after refresh: wait for the cooldown rather than refresh again.
    assert main.transport_load_refresh_time() == NOW + timedelta(hours=4)


def test_empty_available_slot_can_start_but_spent_slot_cannot(outside_item_problem):
    main, board = scenario(
        [None, None, job('running')], [job('good')], stock={ORE: 10},
        remaining=(1, 0, 0), running=(2,), fresh_list=[job('future')],
    )
    scan_list = main.transport_scan_list

    def scan_nonempty_list():
        # Consuming the last known row must not turn the next scan into an OCR failure.
        return scan_list() if board.listed else None

    main.transport_scan_list = scan_nonempty_list
    main.run()
    assert actions(board) == [('swap', 0, 'good'), ('submit', 0), ('refresh',)]
    assert board.remaining == [0, 0, 0]
    assert board.running == {0, 2}
    assert board.primary[1] is not None
    assert board.refreshes == 1


def test_one_usable_trip_with_two_running_needs_no_refresh(outside_item_problem):
    main, board = scenario([job('good')] * 3, stock={ORE: 10}, remaining=(1, 0, 0), running=(1, 2))
    main.run()
    assert actions(board) == [('submit', 0)]


def test_assigned_spent_slots_do_not_force_refresh(outside_item_problem):
    main, board = scenario([job('saved')] * 3, [job('good')], remaining=(0, 0, 0))
    main.run()
    assert actions(board) == []
    assert ('scan_list',) in board.events
    assert main.config.delays == [{'server_update': True}]


@pytest.mark.parametrize('cooldown_hours', [0, 2])
def test_claimed_empty_slots_park_list_jobs_with_spent_trips(outside_item_problem, cooldown_hours):
    main, board = scenario(
        [job('completed')] * 3, [job('good01'), job('good02'), job('good03')],
        stock={ORE: 100}, remaining=(0, 0, 0),
    )
    board.refresh_at = NOW + timedelta(hours=cooldown_hours)

    def claim_rewards():
        board.events.append(('claim',))
        board.primary[:] = [None, None, None]
        return True

    main.transport_claim_rewards = claim_rewards
    main.run()
    assert ('scan_list',) in board.events
    assert actions(board) == [('swap', 0, 'good01'), ('swap', 1, 'good02'), ('swap', 2, 'good03')]
    assert board.remaining == [0, 0, 0]
    assert board.stock == {ORE: 100}
    assert board.running == set()
    assert main.config.calls == []
    assert main.config.delays == [{'server_update': True}]


def test_spent_empty_slots_refresh_after_parking_available_jobs(outside_item_problem):
    main, board = scenario([None, None, None], [job('saved')], stock={ORE: 100}, remaining=(0, 0, 0))
    main.run()
    assert actions(board) == [('swap', 0, 'saved'), ('refresh',)]
    assert board.primary[0].name == 'saved'
    assert all(scanned is not None for scanned in board.primary)
    assert board.remaining == [0, 0, 0]
    assert board.stock == {ORE: 100}
    assert board.running == set()
    assert main.config.calls == []


def test_spent_empty_slots_with_bad_list_refresh_without_submitting(outside_item_problem):
    main, board = scenario(
        [None, None, None], [job('bad', reward=1)], stock={ORE: 100}, remaining=(0, 0, 0),
    )
    main.run()
    assert actions(board) == [('refresh',)]
    assert all(scanned is not None for scanned in board.primary)
    assert board.remaining == [0, 0, 0]
    assert board.refreshes == 1
    assert main.transport_load_refresh_time() == NOW + timedelta(hours=4)


def test_spent_empty_slots_park_during_refresh_cooldown(outside_item_problem):
    main, board = scenario([None, None, None], [job('saved')], remaining=(0, 0, 0))
    board.refresh_at = NOW + timedelta(hours=2)
    main.run()
    assert actions(board) == [('swap', 0, 'saved')]
    assert board.primary[0].name == 'saved'
    assert board.remaining == [0, 0, 0]
    assert board.refreshes == 0
    assert main.next_run_time == NOW + timedelta(hours=2)
    assert main.transport_load_refresh_time() == board.refresh_at


@pytest.mark.parametrize('running, expected_hours', [((), 2), ((2,), 1)])
def test_cooldown_and_batch_collection_schedule(outside_item_problem, running, expected_hours):
    main, board = scenario([job('blocked')] * 3, remaining=(1, 1, 0), running=running)
    board.refresh_at = NOW + timedelta(hours=2)
    main.run()
    assert actions(board) == []
    assert main.next_run_time == NOW + timedelta(hours=expected_hours)
    assert main.transport_load_refresh_time() == board.refresh_at


def test_saved_cooldown_survives_unknown_ui_state(outside_item_problem):
    main, board = scenario([job('blocked')] * 3)
    board.refresh_at = None
    main.transport_save_refresh_time(NOW + timedelta(hours=2))
    main.run()
    assert actions(board) == []
    assert main.next_run_time == NOW + timedelta(hours=2)


def test_dry_run_has_no_mutations(outside_item_problem):
    main, board = scenario([job('bad', reward=1), None, None], [job('blocked')])
    main.run(dry_run=True)
    assert actions(board) == []
    assert ('claim',) not in board.events
    assert main.config.storage == {}


@pytest.mark.parametrize('unknown_part', ['requirements', 'rewards'])
def test_incomplete_recognition_prevents_refresh(outside_item_problem, unknown_part):
    unknown = job('unreadable')
    if unknown_part == 'requirements':
        unknown.unknown = True
    else:
        unknown.rewards.unknown = True
    main, board = scenario([job('bad', reward=1), None, None], [unknown])
    main.run()
    assert actions(board) == []


@pytest.mark.parametrize('remaining', [(1, 1, 1), (0, 0, 0)])
def test_scan_failure_prevents_refresh(outside_item_problem, remaining):
    main, board = scenario([job('bad', reward=1), None, None], remaining=remaining)
    main.transport_scan_list = lambda: None
    main.run()
    assert actions(board) == []


@pytest.mark.parametrize('remaining', [(1, 1, 1), (0, 0, 0)])
def test_unavailable_production_value_prevents_refresh(monkeypatch, remaining):
    monkeypatch.setattr(transport, 'create_production_problem', lambda config: None)
    main, board = scenario([job('bad', reward=1), None, None], [job('blocked')], remaining=remaining)
    main.run()
    assert actions(board) == []


@pytest.mark.parametrize('remaining', [(1, 1, 1), (0, 0, 0)])
def test_solver_failure_prevents_refresh(outside_item_problem, monkeypatch, remaining):
    class FailedOptimizer:
        success = False

        def __init__(self, problem, max_commissions):
            pass

        def select(self, commissions, effective_stock):
            return []

    monkeypatch.setattr(transport, 'TransportOptimizer', FailedOptimizer)
    main, board = scenario([job('bad', reward=1), None, None], [job('blocked')], remaining=remaining)
    main.run()
    assert actions(board) == []


@pytest.mark.parametrize('failure', ['swap', 'submit', 'preservation', 'claim'])
def test_action_failures_suppress_refresh(outside_item_problem, failure):
    if failure == 'preservation':
        main, board = scenario([job('bad', reward=1), None, None], [job('blocked')])
        board.fail_swap = True
    else:
        main, board = scenario([job('bad', reward=1)] * 3, [job('good')], stock={ORE: 10})
        if failure == 'swap':
            board.fail_swap = True
        elif failure == 'submit':
            board.fail_submit = 0
        else:
            main.transport_claim_rewards = lambda: False
    main.run()
    assert board.refreshes == 0
    assert main.next_run_time == NOW + transport.REFRESH_RETRY


def test_failed_post_swap_verification_prevents_submission_and_refresh(outside_item_problem):
    main, board = scenario([job('bad', reward=1)] * 3, [job('good')], stock={ORE: 10})
    main.transport_swap = lambda slot, sub: True
    main.run()
    assert actions(board) == []
    assert board.refreshes == 0


@pytest.mark.parametrize('initial', ['cooldown', 'unknown'])
def test_manual_refresh_requires_enabled_control(initial):
    main = object.__new__(IslandTransport)
    main.config = Config()
    clicks = []
    main.device = SimpleNamespace(click=clicks.append)
    main.transport_list_open = lambda: True
    main.transport_list_close = lambda: True
    main.transport_refresh_status = lambda: (initial, timedelta(hours=2) if initial == 'cooldown' else None)
    assert not main.transport_refresh_list()
    assert clicks == []
    assert main.transport_load_refresh_time() == (NOW + timedelta(hours=2, seconds=3)
                                                if initial == 'cooldown' else None)


def test_manual_refresh_confirms_once_and_verifies_cooldown():
    main = object.__new__(IslandTransport)
    main.config = Config()
    clicks = []
    main.device = SimpleNamespace(click=clicks.append)
    main.transport_list_open = lambda: True
    main.transport_list_close = lambda: True
    states = iter([('ready', None), ('cooldown', timedelta(hours=4))])
    main.transport_refresh_status = lambda: next(states)
    confirmations = iter([True, False])
    main.handle_island_popup_confirm = lambda name: next(confirmations)
    main.handle_transport_popup = lambda: False
    main.appear = lambda *args, **kwargs: True
    main.loop = lambda **kwargs: range(2)
    assert main.transport_refresh_list()
    assert clicks == [transport.ISLAND_TRANSPORT_LIST_REFRESH]
    assert main.transport_load_refresh_time() == NOW + timedelta(hours=4, seconds=3)


def test_next_run_waits_until_all_running_transports_finish(monkeypatch):
    main = object.__new__(IslandTransport)
    monkeypatch.setattr(transport.TRANSPORT_VIEW, 'set', lambda *args, **kwargs: None)
    main.device = SimpleNamespace(screenshot=lambda: None, image=np.zeros((720, 1280, 3), dtype=np.uint8))
    main.slot_running = lambda slot: True
    main.transport_timer_ocr = SimpleNamespace(ocr=lambda *args, **kwargs: [
        timedelta(hours=3), timedelta(minutes=20), timedelta(hours=1),
    ])
    assert main.transport_next_run_time() == NOW + timedelta(hours=3)
