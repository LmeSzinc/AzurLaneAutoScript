from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from module.os.camera import OSCamera


SCREENSHOTS = Path(__file__).resolve().parents[2] / 'collection' / 'os' / 'fleet_walk'


def load_screenshot(name):
    path = SCREENSHOTS / f'{name}.png'
    if not path.is_file():
        pytest.skip(f'Local screenshot fixture is unavailable: {path}')
    with Image.open(path) as screenshot:
        assert screenshot.size == (1280, 720), f'Expected an original-size screenshot: {path}'
        return np.array(screenshot.convert('RGB'))


@pytest.fixture
def camera():
    camera = object.__new__(OSCamera)
    camera.device = SimpleNamespace(image=None)
    return camera


def check_walk_counter(camera, image, now):
    camera.device.image = image
    with patch('module.os.camera.monotonic', return_value=now):
        return camera.walk_counter_changed()


def confirm_walk_counter_baseline(camera, image):
    assert check_walk_counter(camera, image, now=0.) is None
    assert check_walk_counter(camera, image, now=0.25) is True


@pytest.mark.parametrize('first,later,changed', [
    ('stalled_counter_one_jp', 'stalled_counter_one_animated_jp', False),
    ('counter_one_jp', 'counter_one_animated_jp', False),
    ('counter_one_jp', 'counter_two_jp', True),
    ('long_route_counter_one_jp', 'long_route_counter_seven_jp', True),
    ('counter_absent_jp', 'counter_one_jp', True),
    ('counter_one_jp', 'counter_absent_jp', True),
    ('counter_two_jp', 'counter_obscured_jp', True),
])
def test_walk_counter_reports_stable_changes(camera, first, later, changed):
    first, later = load_screenshot(first), load_screenshot(later)
    confirm_walk_counter_baseline(camera, first)

    assert check_walk_counter(camera, later, now=1.) is (None if changed else False)
    assert check_walk_counter(camera, later, now=1.25) is changed
    assert check_walk_counter(camera, later, now=20.) is False
    if changed:
        assert check_walk_counter(camera, first, now=21.) is None
        assert check_walk_counter(camera, first, now=21.25) is True


def test_walk_counter_restarts_confirmation_when_candidate_changes(camera):
    confirm_walk_counter_baseline(camera, load_screenshot('counter_one_jp'))
    changed = load_screenshot('counter_two_jp')

    assert check_walk_counter(camera, changed, now=1.) is None
    assert check_walk_counter(camera, load_screenshot('counter_obscured_jp'), now=1.1) is None
    assert check_walk_counter(camera, changed, now=1.3) is None
    assert check_walk_counter(camera, changed, now=1.55) is True


@pytest.mark.parametrize('transient', [
    'long_route_counter_seven_jp', 'counter_absent_jp', 'counter_obscured_jp',
])
def test_walk_counter_rejects_transient_changes(camera, transient):
    image = load_screenshot('counter_one_jp')
    confirm_walk_counter_baseline(camera, image)

    assert check_walk_counter(camera, load_screenshot(transient), now=1.) is None
    assert check_walk_counter(camera, image, now=1.1) is False
    assert check_walk_counter(camera, image, now=2.) is False


@pytest.mark.parametrize('times', [
    [0., 0.05, 0.1, 0.15, 0.19, 0.21],
    [0., 0.25],
    [0., 1.],
])
def test_walk_counter_confirms_by_elapsed_time(camera, times):
    image = load_screenshot('counter_one_jp')

    for now in times[:-1]:
        assert check_walk_counter(camera, image, now=now) is None
    assert check_walk_counter(camera, image, now=times[-1]) is True


def test_walk_counter_reset_discards_pending_change(camera):
    image = load_screenshot('counter_one_jp')
    confirm_walk_counter_baseline(camera, image)
    assert check_walk_counter(camera, load_screenshot('counter_two_jp'), now=1.) is None

    camera.device.image = None
    assert camera.walk_counter_changed(reset=True) is None

    assert check_walk_counter(camera, image, now=2.) is None
    assert check_walk_counter(camera, image, now=2.25) is True
    assert check_walk_counter(camera, image, now=3.) is False
