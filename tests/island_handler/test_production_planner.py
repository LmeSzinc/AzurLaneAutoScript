from datetime import datetime

import pytest

import module.config.server as server
from module.island.data import DIC_ISLAND_ACTIVITY
from module.island.utils import (
    get_current_activity_list,
    get_current_season_remaining_days,
    get_stuck_season_order_remaining_days,
)
from module.island_handler.production_planner import IslandProductionPlanner


class FakePlannerConfig:
    def __init__(self, values):
        self.values = values

    def cross_get(self, key, default=None):
        return self.values.get(key, default)


class TestIslandProductionPlanner:
    def test_planner_run_replays_with_injected_current_time(self):
        activity = DIC_ISLAND_ACTIVITY[990023]
        start = datetime.strptime(activity['start_time'][server.server], '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(activity['end_time'][server.server], '%Y-%m-%d %H:%M:%S')
        current_time = start + (end - start) / 2
        planner = object.__new__(IslandProductionPlanner)
        planner.config = FakePlannerConfig({
            'IslandProductionPlanner.IslandProductionPlanner.FieldsEfficiency': 0,
            'IslandProductionPlanner.IslandProductionPlanner.OrchardEfficiency': 0,
            'IslandProductionPlanner.IslandProductionPlanner.NurseryEfficiency': 0,
        })

        calculator = planner.run(
            tech_status_yaml={},
            hard_floor_items_yaml={},
            task_target_items={2700: 100},
            stuck_season_order_id=100015,
            export=False,
            current_time=current_time,
        )

        assert calculator.activity_list == get_current_activity_list(current_time)
        assert calculator.task_target_items[2700]['period'] == pytest.approx(
            get_current_season_remaining_days(current_time)
        )
        assert calculator.stuck_season_order_id == 100060
        assert calculator.stuck_season_order_items[4011]['period'] == pytest.approx(
            get_stuck_season_order_remaining_days(100015, current_time)
        )
