from pathlib import Path
from types import SimpleNamespace

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


def check_walk_counter(camera, image):
    camera.device.image = image
    return camera.walk_counter_changed()


@pytest.mark.parametrize('first,later,changed', [
    ('stalled_counter_one_jp', 'stalled_counter_one_animated_jp', False),
    ('counter_one_jp', 'counter_one_animated_jp', False),
    ('counter_one_jp', 'counter_two_jp', True),
    ('long_route_counter_one_jp', 'long_route_counter_seven_jp', True),
    ('counter_absent_jp', 'counter_one_jp', True),
    ('counter_one_jp', 'counter_absent_jp', True),
    ('counter_two_jp', 'counter_obscured_jp', True),
    ('reference/93/counter_01_jp', 'reference/93/counter_10_jp', True),
    ('obscured/93/frame_000036_jp', 'obscured/93/frame_000053_jp', False),
    ('obscured/93/frame_000053_jp', 'obscured/93/frame_000069_jp', True),
])
def test_walk_counter_reports_changes(camera, first, later, changed):
    first, later = load_screenshot(first), load_screenshot(later)
    assert check_walk_counter(camera, first) is True
    assert check_walk_counter(camera, first) is False
    assert check_walk_counter(camera, later) is changed
    assert check_walk_counter(camera, later) is False
    if changed:
        assert check_walk_counter(camera, first) is True


def test_walk_counter_reset_discards_reference(camera):
    image = load_screenshot('counter_one_jp')
    assert check_walk_counter(camera, image) is True
    assert check_walk_counter(camera, image) is False

    camera.device.image = None
    assert camera.walk_counter_changed(reset=True) is None

    assert check_walk_counter(camera, image) is True
    assert check_walk_counter(camera, image) is False
