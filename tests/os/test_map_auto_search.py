from functools import partial
from types import SimpleNamespace
from unittest.mock import Mock

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
        return device.image.get('auto', 'on') == {
            map_module.AUTO_SEARCH_OS_MAP_OPTION_ON: 'on',
            map_module.AUTO_SEARCH_OS_MAP_OPTION_OFF: 'off',
            map_module.AUTO_SEARCH_OS_MAP_OPTION_OFF_DISABLED: 'disabled',
        }.get(button)

    main = SimpleNamespace(
        device=device, loop=loop,
        is_in_map=lambda: device.image.get('page', 'map') == 'map',
        match_template_color=match, appear=match,
        get_walk_counter=Mock(side_effect=lambda: device.image.get('counter', 0)),
        hp_reset=Mock(), on_auto_search_battle_count_reset=Mock(),
        on_auto_search_battle_count_add=Mock(),
        handle_os_auto_search_map_option=lambda **kwargs: device.image.get('option', False),
        handle_retirement=lambda: device.image.get('retirement', False),
        combat_appear=lambda: device.image.get('combat', False),
        auto_search_combat=lambda **kwargs: True,
        handle_map_event=lambda: device.image.get('event', False),
    )
    return main, clock


@pytest.mark.parametrize('frames,clears', [
    ([{}] * 80, 2),
    ([{'counter': 1}] * 80, 3),
    ([{'counter': 2}] * 80, 3),
    ([{'counter': 3}] * 80, 3),
    ([{'counter': 1}, {'page': 'loading'}] * 40, 3),
    ([{'counter': 1}, {'auto': 'unknown'}] * 40, 3),
], ids=['absent', 'one', 'two', 'three', 'map-flicker', 'auto-flicker'])
def test_auto_search_without_progress_triggers_stuck_guard(monkeypatch, frames, clears):
    main, clock = make_auto_search(monkeypatch, frames)

    with pytest.raises(GameStuckError):
        map_module.OSMap.os_auto_search_daemon(main)

    assert clock.now >= 1060
    assert main.device.stuck_record_clear.call_count == clears


def test_auto_search_clears_only_on_counter_changes(monkeypatch):
    frames = [{'counter': value} for value in (0, 0, 1, 1, 2, 0, 0, 3)]
    main, _ = make_auto_search(monkeypatch, frames)

    assert map_module.OSMap.os_auto_search_daemon(main) == 0
    assert main.device.stuck_record_clear.call_count == 5


def test_auto_search_allows_continuous_wandering(monkeypatch):
    frames = [{'counter': index // 4 % 4} for index in range(240)]
    main, clock = make_auto_search(monkeypatch, frames)

    assert map_module.OSMap.os_auto_search_daemon(main) == 0
    assert clock.now == 1240
    assert main.device.stuck_record_clear.call_count == 60


@pytest.mark.parametrize('transition,reads', [
    ({'page': 'loading'}, 2),
    ({'auto': 'off'}, 2),
    ({'auto': 'disabled'}, 2),
    ({'auto': 'unknown'}, 2),
    ({'option': True}, 3),
    ({'retirement': True}, 3),
    ({'combat': True}, 3),
    ({'event': True}, 3),
])
def test_auto_search_retains_counter_across_transitions(monkeypatch, transition, reads):
    frames = [{'counter': 1}, dict(counter=1, **transition), {'counter': 1}]
    main, _ = make_auto_search(monkeypatch, frames)

    assert map_module.OSMap.os_auto_search_daemon(main) == int(transition.get('combat', False))
    assert main.get_walk_counter.call_count == reads
    assert main.device.stuck_record_clear.call_count == 2
