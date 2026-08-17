"""Unit tests for module.core.geometry.fit_points (moved in P2.1).

fit_points fits the best point on a periodic grid (common difference `mod`)
for a set of noisy observations; the implementation moved verbatim from
module.map_detection.utils, so these tests pin its behavior.
"""

import numpy as np

from module.core.geometry import fit_points


def test_result_within_grid_period():
    # fit_points returns `optimize.brute(...) % mod`: a float point inside
    # the [0, mod) period, near one of the observed modulo clusters.
    rng = np.random.default_rng(0)
    points = rng.integers(0, 30, size=(8, 2)) * 10 + rng.integers(0, 3, size=(8, 2))
    result = fit_points(points, mod=(10, 10), encourage=1)
    assert result.shape == (2,)
    assert np.all(result >= -1e-6)
    assert np.all(result < 10)
    clusters = np.unique(points % 10, axis=0)
    nearest = np.min(np.abs(np.round(result) - clusters), axis=0)
    assert np.all(nearest <= 1)


def test_fit_lands_on_tight_cluster():
    # A tight cluster around (17, 23) with a large mod: the fitted point
    # stays close to the cluster mean (modulo the grid).
    points = np.array([[17, 23], [18, 22], [16, 24], [19, 23]])
    result = fit_points(points, mod=(100, 100), encourage=1)
    mean = np.round(points.mean(axis=0)).astype(int)
    assert abs(result[0] - mean[0]) <= 2
    assert abs(result[1] - mean[1]) <= 2


def test_deterministic():
    rng = np.random.default_rng(42)
    points = rng.integers(0, 100, size=(20, 2))
    assert np.array_equal(fit_points(points, mod=(50, 50)), fit_points(points, mod=(50, 50)))


def test_single_point():
    points = np.array([[5, 7]])
    result = fit_points(points, mod=(10, 10), encourage=1)
    assert result.shape == (2,)
    # A single observation pins the fit to the point itself, modulo the period
    assert np.all(np.abs(result - (points[0] % 10)) < 1)
