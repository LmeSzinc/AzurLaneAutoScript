from datetime import timedelta
from types import SimpleNamespace

import pytest

from module.island.assets import (
    ISLAND_ORDER_ACCEPT,
    ISLAND_ORDER_COOLDOWN_SPEED_UP,
    ISLAND_ORDER_REQUIREMENTS_CHECK,
)
from module.island.order import IslandOrder


def make_order(monkeypatch, panel, selected_from):
    state = SimpleNamespace(now=100.0, frame=-1, clicks=[])
    monkeypatch.setattr('module.base.timer.time', lambda: state.now)
    main = object.__new__(IslandOrder)

    def screenshot():
        state.now += 0.25
        state.frame += 1
        main.device.image = state.frame

    main.device = SimpleNamespace(
        image=-1,
        screenshot=screenshot,
        click=lambda button: state.clicks.append((state.frame, button)),
    )
    main.is_order_selected = lambda button: state.frame >= selected_from
    main.appear = lambda button, **kwargs: button is panel
    return main, state


@pytest.mark.parametrize('panel', [ISLAND_ORDER_REQUIREMENTS_CHECK, ISLAND_ORDER_COOLDOWN_SPEED_UP])
def test_click_order_waits_for_target_selection(monkeypatch, panel):
    main, state = make_order(monkeypatch, panel, selected_from=4)
    target = object()

    assert main.click_order(target) is True
    assert state.frame == 4
    assert state.clicks == [(0, target)]


def test_click_order_retries_wrong_type_and_reports_timeout(monkeypatch):
    main, state = make_order(monkeypatch, ISLAND_ORDER_ACCEPT, selected_from=0)
    target = object()

    assert main.click_order(target, is_urgent=True) is False
    assert len(state.clicks) >= 3
    assert all(button is target for _, button in state.clicks)
    assert state.now >= 105


def test_execute_order_does_not_read_unconfirmed_requirements():
    main = object.__new__(IslandOrder)
    main.handle_island_additional = lambda: False
    main.handle_info_bar = lambda: False
    main.click_order = lambda *args, **kwargs: False
    main.appear = lambda *args, **kwargs: pytest.fail('Unconfirmed order panel inspected')
    main.scan_current_order_requirements = lambda: pytest.fail('Unconfirmed requirements scanned')

    assert main.execute_order(object()) is False


def test_cooldown_fallback_does_not_read_unconfirmed_panel(monkeypatch):
    main = object.__new__(IslandOrder)
    delays = []
    main.config = SimpleNamespace(task_delay=lambda **kwargs: delays.append(kwargs))
    main.device = SimpleNamespace(image=object())
    main.ui_ensure = lambda page: None
    main.detect_all_orders = lambda: None
    main.run_any_order = lambda: False
    main.season_orders = [object()]
    main.regular_cooldown_orders = [object()]
    main.get_order_remain_time = lambda button: timedelta(0)
    main.click_order = lambda button: False
    monkeypatch.setattr(IslandOrder, 'cooldown_time_ocr', property(
        lambda self: pytest.fail('Unconfirmed cooldown scanned')))

    main.run()

    assert main.next_runtime == []
    assert delays == [{'server_update': True}]
