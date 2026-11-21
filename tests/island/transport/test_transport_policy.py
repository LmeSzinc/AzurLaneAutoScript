"""Tests for the decision logic of the island transport module."""

import pytest

import module.island.transport as transport
from module.island.data import DIC_ISLAND_ITEM
from module.island.transport import IslandTransport, ScannedCommission, adjust_counter, assign_swaps


def item(name):
    return next(item_id for item_id, data in DIC_ISLAND_ITEM.items() if data['name']['en'] == name)


def commission(name, submissions, stock, slot=None, index=None, rewards=None):
    scanned = ScannedCommission(name, slot=slot, index=index)
    scanned.submissions = [(item(item_name), need) for item_name, need in submissions]
    scanned.stock = {item(item_name): amount for item_name, amount in stock.items()}
    scanned.rewards = {item(item_name): count for item_name, count in (rewards or {}).items()}
    return scanned


def fish_module(hard_floor=None):
    module = object.__new__(IslandTransport)
    module.hard_floor = hard_floor or {}
    module.reserve = {}
    return module


@pytest.mark.parametrize('counter, spilled, covered, expected', [
    ((518, 7), False, False, (518, 7)),
    ((518, 7), False, True, (518, 9)),
    ((82, 15), False, True, (82, 19)),
    # IslandReversedDigitCounter reads 518/ as 518/0
    ((518, 0), False, True, (518, 9)),
    ((126655, 29), True, False, (126655, 29)),
    ((6655, 29), True, False, (10000, 29)),
    ((29, 29), True, False, (10000, 29)),
])
def test_adjust_counter(counter, spilled, covered, expected):
    assert adjust_counter(*counter, spilled=spilled, covered=covered) == expected


def test_assign_swaps_fills_blocked_slots_first():
    assert assign_swaps([0, 1, 2], chosen_slots=[1], chosen_subs=['01', '05'], blocked_slots=[2]) \
        == [(2, '01'), (0, '05')]
    assert assign_swaps([0, 2], chosen_slots=[0, 2], chosen_subs=['01'], blocked_slots=[]) == []


def test_needs_fish_meat_only_for_submissions():
    reward_only = commission('01', [('Onion', 6)], {'Onion': 84}, index=1, rewards={'Freshwater Fish Meat': 11})
    submit = commission('P3', [('Saltwater Fish Meat', 4)], {'Saltwater Fish Meat': 1}, slot=2)
    assert not fish_module().needs_fish_meat([reward_only], max_commissions=3)
    assert fish_module().needs_fish_meat([reward_only, submit], max_commissions=3)


def test_needs_fish_meat_largest_needs():
    fish = 'Freshwater Fish Meat'
    commissions = [
        commission('P1', [(fish, 10)], {fish: 20}, slot=0),
        commission('01', [(fish, 5), ('Onion', 6)], {fish: 20, 'Onion': 84}, index=1),
        commission('02', [(fish, 8)], {fish: 20}, index=2),
    ]
    # Largest 2 needs are 10 + 8
    assert not fish_module().needs_fish_meat(commissions, max_commissions=2)
    assert fish_module().needs_fish_meat(commissions, max_commissions=3)
    # Effective stock 20 - 5 is short of 18
    assert fish_module(hard_floor={item(fish): 5}).needs_fish_meat(commissions, max_commissions=2)
    # Commissions with unknown items are not chosen
    commissions[0].unknown = True
    assert not fish_module().needs_fish_meat(commissions, max_commissions=3)


def test_decide_swaps_into_blocked_slot(monkeypatch):
    class FakeOptimizer:
        success = True

        def __init__(self, problem, max_commissions):
            FakeOptimizer.max_commissions = max_commissions

        def select(self, commissions, effective_stock):
            FakeOptimizer.names = [c.name for c in commissions]
            FakeOptimizer.effective_stock = effective_stock
            return [FakeOptimizer.names.index('P2'), FakeOptimizer.names.index('03')]

    monkeypatch.setattr(transport, 'create_production_problem', lambda config: {})
    monkeypatch.setattr(transport, 'TransportOptimizer', FakeOptimizer)
    module = object.__new__(IslandTransport)
    module.config = object()
    module.hard_floor = {item('Milk'): 0}
    module.reserve = {}
    slots = {
        0: commission('P1', [('Onion', 7)], {'Onion': 100}, slot=0),
        1: commission('P2', [('Flax', 26)], {'Flax': 185}, slot=1),
        2: commission('P3', [('Milk', 7)], {'Milk': 0}, slot=2),
    }
    unknown = commission('01', [('Apple', 19)], {'Apple': 219}, index=1)
    unknown.unknown = True
    subs = {1: unknown, 3: commission('03', [('Mango', 8)], {'Mango': 30}, index=3)}

    swaps, submit = module.transport_decide(slots, subs)
    assert FakeOptimizer.max_commissions == 3
    # Commissions with unknown items are not valued
    assert FakeOptimizer.names == ['P1', 'P2', 'P3', '03']
    assert FakeOptimizer.effective_stock[item('Milk')] == 0
    # P3 can't be submitted with no Milk, so 03 replaces it rather than P1
    assert [(slot, sub.name) for slot, sub in swaps] == [(2, '03')]
    assert submit == [1, 2]


class FakeTaskConfig:
    def __init__(self):
        self.calls = []
        self.storage = {}

    def cross_get(self, key, default=None):
        return self.storage.get(key, default)

    def cross_set(self, key, value):
        self.storage[key] = value

    def task_delay(self, **kwargs):
        self.calls.append(('task_delay', kwargs))

    def task_call(self, task, force_call=True):
        self.calls.append(('task_call', task, force_call))


def run_module(submit=(), submit_success=True):
    """
    IslandTransport whose run() decides to submit the given slots.

    Args:
        submit (tuple[int]): Slots to submit.
        submit_success (bool): Result of each submit.
    """
    module = object.__new__(IslandTransport)
    module.config = FakeTaskConfig()
    module.submitted = []
    module.server_support_island_transport = lambda: True
    module.ui_ensure = lambda page: None
    module.transport_claim_rewards = lambda: True
    module.transport_scan_slots = lambda rewards=True: ({}, {})
    module.needs_fish_meat = lambda commissions, max_commissions: False
    module.transport_decide = lambda slots, subs: ([], list(submit)) if submit else None
    module.transport_submit = lambda slot: module.submitted.append(slot) or submit_success
    module.transport_next_run_time = lambda: None
    return module


def task_calls(module):
    return [call for call in module.config.calls if call[0] == 'task_call']


def test_unknown_commissions_do_not_trigger_swaps():
    module = run_module()
    primary = commission('P1', [('Onion', 7)], {'Onion': 100}, slot=0)
    listed = commission('01', [('Apple', 19)], {'Apple': 219}, index=1)
    primary.unknown = listed.unknown = True
    module.transport_scan_slots = lambda rewards=True: (['ready'], {0: primary})
    module.transport_scan_list = lambda: {1: listed}
    swapped = []
    module.transport_swap = lambda slot, sub: swapped.append((slot, sub.name)) or True

    module.run()

    assert swapped == []
    assert module.submitted == []


def test_submit_calls_island_order():
    module = run_module(submit=(0, 2))
    module.run()
    assert module.submitted == [0, 2]
    # IslandOrder is called once after the delay, and only if the user enabled it
    assert module.config.calls[-1] == ('task_call', 'IslandOrder', False)
    assert task_calls(module) == [('task_call', 'IslandOrder', False)]


@pytest.mark.parametrize('submit, submit_success, dry_run', [
    # Nothing to submit
    ((), True, False),
    # Submit timeout
    ((0,), False, False),
    # Decided but not submitted
    ((0,), True, True),
])
def test_no_submit_does_not_call_island_order(submit, submit_success, dry_run):
    module = run_module(submit=submit, submit_success=submit_success)
    module.run(dry_run=dry_run)
    assert task_calls(module) == []
