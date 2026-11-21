from datetime import datetime, timedelta
from types import SimpleNamespace

import module.island.business as business
import module.island_handler.restaurant as restaurant


NOW = datetime(2026, 10, 29, 10, 0, 0)


class FixedDateTime:
    @classmethod
    def now(cls):
        return NOW


class FakeButton:
    def crop(self, area):
        return self


def make_business(monkeypatch, states, outcomes, midnight_offsets, remain=None):
    restaurant_ids = tuple(business.RESTAURANT_IDS)
    states = {restaurant_id: states.get(restaurant_id, 'skip')
              for restaurant_id in restaurant_ids}
    monkeypatch.setattr(business, 'datetime', FixedDateTime)
    offsets = iter(midnight_offsets)
    monkeypatch.setattr(
        business,
        'get_server_next_update',
        lambda _: NOW + next(offsets),
    )

    main = object.__new__(business.IslandBusiness)
    state = SimpleNamespace(index=0, flags=[], delays=[])
    main.config = SimpleNamespace(task_delay=lambda target: state.delays.append(target))
    main.skip_restaurant = {
        restaurant_id: states[restaurant_id] == 'skip'
        for restaurant_id in restaurant_ids
    }
    main.device = SimpleNamespace(click=lambda button: None)
    main.loop = lambda **kwargs: [0]
    main.ui_ensure = lambda *args, **kwargs: None
    main.island_manage_side_navbar_ensure = lambda **kwargs: None
    main.handle_restaurant_popup = lambda: None
    main.restaurant_swipe_to_top = lambda: None
    main.restaurant_swipe_to_bottom = lambda: None
    main.ui_back = lambda *args, **kwargs: None
    main.current_restaurant_button = lambda: (
        FakeButton() if state.index < len(restaurant_ids) else None
    )
    main.get_restaurant_id = lambda button: restaurant_ids[state.index]
    main.next_restaurant = lambda: setattr(state, 'index', state.index + 1)
    main.is_restaurant_running = lambda button: states[restaurant_ids[state.index]] == 'running'
    main.is_restaurant_resting = lambda button: states[restaurant_ids[state.index]] == 'resting'
    main.get_remain_time = lambda button: remain or timedelta(hours=1)
    main.appear = lambda *args, **kwargs: True

    def fake_restaurant_run(module):
        restaurant_id = module.working_restaurant_id
        state.flags.append((restaurant_id, module.waitress_occupied))
        outcome = outcomes[restaurant_id]
        if outcome == 'occupied':
            module.waitress_occupied = True
        return outcome == 'success'

    monkeypatch.setattr(restaurant.IslandRestaurant, 'run', fake_restaurant_run)
    return main, state


def test_occupied_failure_schedules_eight_hour_retry(monkeypatch):
    main, state = make_business(
        monkeypatch,
        {601: 'ready'},
        {601: 'occupied'},
        [timedelta(hours=12)],
    )

    main.run()

    assert state.delays == [NOW + timedelta(hours=8)]
    assert state.flags == [(601, False)]


def test_occupied_retry_keeps_earlier_daily_deadline(monkeypatch):
    main, state = make_business(
        monkeypatch,
        {601: 'ready'},
        {601: 'occupied'},
        [timedelta(hours=4)],
    )

    main.run()

    assert state.delays == [NOW + timedelta(hours=4)]


def test_ordinary_failure_keeps_midnight_deadline(monkeypatch):
    main, state = make_business(
        monkeypatch,
        {601: 'ready'},
        {601: 'failed'},
        [timedelta(hours=12)],
    )

    main.run()

    assert state.delays == [NOW + timedelta(hours=12)]
    assert state.flags == [(601, False)]


def test_running_restaurant_earlier_completion_wins_over_occupied_retry(monkeypatch):
    main, state = make_business(
        monkeypatch,
        {601: 'running', 602: 'ready'},
        {601: 'failed', 602: 'occupied'},
        [timedelta(hours=12), timedelta(hours=12)],
        remain=timedelta(hours=2),
    )

    main.run()

    assert state.delays == [NOW + timedelta(hours=2)]
    assert state.flags == [(602, False)]


def test_busy_flag_resets_before_each_restaurant(monkeypatch):
    main, state = make_business(
        monkeypatch,
        {601: 'ready', 602: 'ready'},
        {601: 'occupied', 602: 'failed'},
        [timedelta(hours=12), timedelta(hours=4)],
    )

    main.run()

    assert state.delays == [NOW + timedelta(hours=4)]
    assert state.flags == [(601, False), (602, False)]
