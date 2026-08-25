"""Tests for island production utility functions."""
from module.island.utils import get_idle_accumulating_batch_count


class TestGetIdleAccumulatingBatchCount:
    def test_batch_equal_to_quantum(self):
        # Cutlery-like recipe: 6h per batch, 6h quantum -> single batch,
        # instead of a full 30h production queue
        assert get_idle_accumulating_batch_count(216000, 6) == 1

    def test_short_batches_fill_quantum(self):
        # 0.6h per batch -> 10 batches fit in 6h
        assert get_idle_accumulating_batch_count(21600, 6) == 10

    def test_quantum_is_upper_bound(self):
        # 4h per batch: two batches (8h) would exceed the 6h quantum -> 1
        assert get_idle_accumulating_batch_count(144000, 6) == 1

    def test_batch_longer_than_quantum_still_runs_one(self):
        # 8h per batch exceeds the quantum by itself, still dispatch one
        assert get_idle_accumulating_batch_count(288000, 6) == 1

    def test_invalid_workload(self):
        assert get_idle_accumulating_batch_count(0, 6) == 1
        assert get_idle_accumulating_batch_count(-1, 6) == 1
