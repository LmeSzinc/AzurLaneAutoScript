"""Tests for island production utility functions."""
from datetime import datetime

import pytest

import module.config.server as server
from module.island.data import DIC_ISLAND_ACTIVITY
from module.island.utils import (
    get_current_season_remaining_days,
    get_idle_accumulating_batch_count,
    get_stuck_season_order_remaining_days,
    get_task_target_items,
)


class FakeConfig:
    def __init__(self, values):
        self.values = values

    def cross_get(self, key, default=None):
        return self.values.get(key, default)


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


def test_get_task_target_items_merges_config_and_stuck_order_at_injected_time():
    activity = DIC_ISLAND_ACTIVITY[990023]
    start = datetime.strptime(activity['start_time'][server.server], '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime(activity['end_time'][server.server], '%Y-%m-%d %H:%M:%S')
    current_time = start + (end - start) / 2
    config = FakeConfig({
        'IslandSeasonTask.IslandSeasonTask.TaskTarget': '2700: 100',
        'IslandOrder.IslandOrder.StuckSeasonOrderId': 100015,
    })

    items = get_task_target_items(config, current_time=current_time)

    assert items[2700]['total_need_count'] == 100
    assert items[2700]['period'] == pytest.approx(
        get_current_season_remaining_days(current_time)
    )
    for item_id in (4011, 4013):
        assert items[item_id]['total_need_count'] == 5
        assert items[item_id]['period'] == pytest.approx(
            get_stuck_season_order_remaining_days(100015, current_time)
        )
