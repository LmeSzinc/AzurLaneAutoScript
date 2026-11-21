from datetime import datetime

import pytest

import module.config.server as server
from module.island.season_data import DIC_ISLAND_ACTIVITY
from module.island.utils import (
    get_configured_season,
    get_season_remaining_days,
    get_stuck_season_order_remaining_days,
)
from module.island_handler.milp import milp
from module.island_handler.production_planner import (
    IslandProductionPlanner,
    create_production_calculator,
    create_production_problem,
    load_planner_demands,
)


class FakePlannerConfig:
    def __init__(self, values):
        self.values = values

    def cross_get(self, key, default=None):
        return self.values.get(key, default)


class TestIslandProductionPlanner:
    @pytest.mark.parametrize('srv', ['cn', 'tw'])
    def test_planner_run_uses_configured_season(self, monkeypatch, srv):
        monkeypatch.setattr(server, 'server', srv)
        activity = DIC_ISLAND_ACTIVITY[990023]
        start = datetime.strptime(activity['start_time'][server.server], '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(activity['end_time'][server.server], '%Y-%m-%d %H:%M:%S')
        current_time = start + (end - start) / 2
        monkeypatch.setattr('module.island.utils._get_server_time', lambda time=None: current_time)
        planner = object.__new__(IslandProductionPlanner)
        planner.config = FakePlannerConfig({
            'IslandGeneral.IslandGeneral.Season': 'season_20260806_cn',
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
        )

        season = get_configured_season(planner.config)
        assert calculator.season == season
        assert calculator.task_target_items[2700]['period'] == pytest.approx(
            get_season_remaining_days(season, current_time)
        )
        assert calculator.stuck_season_order_id == 100060
        assert calculator.stuck_season_order_items[4011]['period'] == pytest.approx(
            get_stuck_season_order_remaining_days(100060, current_time)
        )


class TestPlannerConfig:
    @staticmethod
    def season_midpoint():
        activity = DIC_ISLAND_ACTIVITY[990023]
        start = datetime.strptime(activity['start_time'][server.server], '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(activity['end_time'][server.server], '%Y-%m-%d %H:%M:%S')
        return start + (end - start) / 2

    @staticmethod
    def planner_config(**values):
        config = {
            'IslandGeneral.IslandGeneral.Season': 'season_20260806_cn',
            'IslandProductionPlanner.IslandProductionPlanner.FieldsEfficiency': 0,
            'IslandProductionPlanner.IslandProductionPlanner.OrchardEfficiency': 0,
            'IslandProductionPlanner.IslandProductionPlanner.NurseryEfficiency': 0,
            'IslandProductionPlanner.Storage.Storage.IslandTechnologyStatus': {},
            'IslandSeasonTask.IslandSeasonTask.TaskTarget': '{2700: 100}',
            'IslandOrder.IslandOrder.StuckSeasonOrderId': 100015,
        }
        config.update(values)
        return FakePlannerConfig(config)

    def test_load_planner_demands(self, monkeypatch):
        current_time = self.season_midpoint()
        monkeypatch.setattr('module.island.utils._get_server_time', lambda time=None: current_time)
        config = self.planner_config()
        assert load_planner_demands(config) == {
            'task_target_items': {2700: 100},
            'task_target_period': get_season_remaining_days(get_configured_season(config), current_time),
            'stuck_season_order_id': 100015,
        }
        # Given values win over config
        demands = load_planner_demands(config, task_target_items={}, stuck_season_order_id=0)
        assert demands['task_target_items'] == {}
        assert demands['stuck_season_order_id'] == 0

    def test_create_production_problem_matches_planner_run(self, monkeypatch):
        current_time = self.season_midpoint()
        monkeypatch.setattr('module.island.utils._get_server_time', lambda time=None: current_time)
        config = self.planner_config()
        planner = object.__new__(IslandProductionPlanner)
        planner.config = config
        solved = planner.run(hard_floor_items_yaml={}, export=False)

        problem = create_production_problem(config)
        assert problem['demand_items'] == solved.demand_items
        assert problem['stuck_season_order_id'] == solved.stuck_season_order_id == 100060
        result = milp(problem['c'], constraints=problem['constraints'], bounds=problem['bounds'])
        rebuilt = create_production_calculator(config, {})
        rebuilt._apply_production_lp_result(result, problem)
        assert rebuilt.lp_success
        assert rebuilt.production_plan == pytest.approx(solved.production_plan)
        assert rebuilt.net_items == pytest.approx(solved.net_items)

    def test_create_production_problem_needs_saved_technology(self):
        config = self.planner_config(**{'IslandProductionPlanner.Storage.Storage.IslandTechnologyStatus': None})
        assert create_production_problem(config) is None
