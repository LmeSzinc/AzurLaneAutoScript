from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from module.os.camera import OSCamera


SCREENSHOTS = Path(__file__).resolve().parents[2] / 'collection' / 'os' / 'fleet_walk'


@pytest.mark.parametrize('name,expected', [
    (f'reference/93/counter_{value:02d}_jp', value if value <= 3 else 0)
    for value in range(1, 11)
] + [
    ('stalled_counter_one_jp', 1),
    ('stalled_counter_one_animated_jp', 1),
    ('counter_one_jp', 1),
    ('counter_one_animated_jp', 1),
    ('counter_two_jp', 2),
    ('counter_three_reference_jp', 3),
    ('long_route_counter_one_jp', 1),
    ('long_route_counter_seven_jp', 0),
    ('counter_absent_jp', 0),
    ('counter_obscured_jp', 0),
    ('obscured/93/frame_000036_jp', 1),
    ('obscured/93/frame_000069_jp', 2),
] + [
    (f'stalled_104/frame_{frame:06d}_jp', 0) for frame in (0, 17, 25, 26, 39)
])
def test_get_walk_counter(name, expected):
    path = SCREENSHOTS / f'{name}.png'
    if not path.is_file():
        pytest.skip(f'Local screenshot fixture is unavailable: {path}')
    with Image.open(path) as screenshot:
        assert screenshot.size == (1280, 720)
        image = np.array(screenshot.convert('RGB'))
    camera = object.__new__(OSCamera)
    camera.device = SimpleNamespace(image=image)

    assert camera.get_walk_counter() == expected
