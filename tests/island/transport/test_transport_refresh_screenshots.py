"""Transport list refresh controls and cooldown OCR from real captures."""

from module.island.assets import ISLAND_TRANSPORT_LIST_REFRESH, ISLAND_TRANSPORT_LIST_REFRESH_COOLDOWN
from module.island.transport import IslandTransport, REFRESH_TIMER_AREA
from module.testing.screenshot import image


def refresh_snapshot(main):
    state, remain = main.transport_refresh_status()
    actual = {'state': state, 'remaining_seconds': int(remain.total_seconds()) if remain is not None else None}
    main.device.review(actual, [
        (ISLAND_TRANSPORT_LIST_REFRESH.area, 'list refresh {}'.format(state)),
        (ISLAND_TRANSPORT_LIST_REFRESH_COOLDOWN.area, 'cooldown indicator'),
        (REFRESH_TIMER_AREA, 'cooldown {}'.format(actual['remaining_seconds'])),
    ])
    return actual


@image('island/transport/list_refresh_available_jp.webp', server='jp')
def test_refresh_available_jp(main: IslandTransport):
    assert refresh_snapshot(main) == {'state': 'ready', 'remaining_seconds': None}


@image('island/transport/list_refresh_cooldown_long_jp.webp', server='jp')
def test_refresh_cooldown_long_jp(main: IslandTransport):
    assert refresh_snapshot(main) == {'state': 'cooldown', 'remaining_seconds': 13370}


@image('island/transport/list_refresh_cooldown_short_jp.webp', server='jp')
def test_refresh_cooldown_short_jp(main: IslandTransport):
    assert refresh_snapshot(main) == {'state': 'cooldown', 'remaining_seconds': 7513}
