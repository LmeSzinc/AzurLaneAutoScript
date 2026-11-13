from functools import partial
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

import module.base.timer as timer_module
import module.os.map as map_module
from module.base.timer import Timer
from module.device.device import Device
from module.exception import GameStuckError


def make_auto_search(monkeypatch, frames):
    clock = SimpleNamespace(now=1000.)
    monkeypatch.setattr(timer_module, 'time', lambda: clock.now)
    device = SimpleNamespace(
        image=None, detect_record=set(), stuck_long_wait_list=[],
        stuck_timer=Timer(60, count=60).start(),
        stuck_timer_long=Timer(180, count=180).start(),
        app_is_running=lambda: True,
    )
    device.stuck_record_clear = Mock(wraps=partial(Device.stuck_record_clear, device))

    def loop():
        for frame in frames:
            clock.now += 1
            Device.stuck_record_check(device)
            device.image = frame
            yield

    def match(button, **kwargs):
        if device.image.get('page', 'map') != 'map':
            return False
        state = device.image.get('auto', 'on')
        return state == {
            map_module.AUTO_SEARCH_OS_MAP_OPTION_ON: 'on',
            map_module.AUTO_SEARCH_OS_MAP_OPTION_OFF: 'off',
            map_module.AUTO_SEARCH_OS_MAP_OPTION_OFF_DISABLED: 'disabled',
        }.get(button)

    main = SimpleNamespace(
        device=device,
        loop=loop,
        is_in_map=lambda: device.image.get('page', 'map') == 'map',
        match_template_color=match, appear=match,
        walk_counter_changed=Mock(
            side_effect=lambda reset=False: None if reset else device.image.get('progress', False)),
        hp_reset=Mock(),
        on_auto_search_battle_count_reset=Mock(),
        on_auto_search_battle_count_add=Mock(),
        handle_os_auto_search_map_option=lambda **kwargs: device.image.get('option', False),
        handle_retirement=lambda: device.image.get('retirement', False),
        combat_appear=lambda: device.image.get('combat', False),
        auto_search_combat=lambda **kwargs: True,
        handle_map_event=lambda: device.image.get('event', False),
    )
    return main, clock


@pytest.mark.parametrize('frames', [
    [{'progress': False}] * 80,
    [{'progress': None}] * 80,
    [{'progress': False}, {'progress': None}] * 40,
    [{'page': 'loading'}] * 80,
    [{'auto': 'unknown'}] * 80,
], ids=['unchanged', 'unconfirmed', 'intermittent', 'loading', 'unknown-auto'])
def test_auto_search_without_progress_triggers_stuck_guard(monkeypatch, frames):
    main, clock = make_auto_search(monkeypatch, [{'progress': True}] + frames)

    with pytest.raises(GameStuckError):
        map_module.OSMap.os_auto_search_daemon(main)

    assert clock.now >= 1060
    assert main.device.stuck_record_clear.call_count == 3


def test_auto_search_allows_continuous_wandering(monkeypatch):
    frames = [{'progress': index % 4 == 0} for index in range(240)]
    main, clock = make_auto_search(monkeypatch, frames)

    assert map_module.OSMap.os_auto_search_daemon(main) == 0

    assert clock.now == 1240
    assert main.device.stuck_record_clear.call_count == 61


@pytest.mark.parametrize('transition,transition_calls', [
    ({'page': 'loading'}, [call(reset=True)]),
    ({'auto': 'off'}, [call(reset=True)]),
    ({'auto': 'disabled'}, [call(reset=True)]),
    ({'option': True}, [call(), call(reset=True)]),
    ({'retirement': True}, [call(), call(reset=True)]),
    ({'combat': True}, [call(), call(reset=True)]),
    ({'event': True}, [call(), call(reset=True)]),
    ({'auto': 'unknown'}, []),
])
def test_auto_search_resets_counter_only_on_transitions(monkeypatch, transition, transition_calls):
    main, _ = make_auto_search(monkeypatch, [{}, transition, {}])

    assert map_module.OSMap.os_auto_search_daemon(main) == int(transition.get('combat', False))

    assert main.walk_counter_changed.call_args_list == [call(reset=True), call()] + transition_calls + [call()]
