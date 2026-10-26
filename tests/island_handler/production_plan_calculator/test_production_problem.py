import numpy as np
import pytest

from module.island.data import DIC_ISLAND_ITEM
from module.island_handler.milp import LinearConstraint, milp
from module.island_handler.production_plan_calculator import extend_problem

EPS = 1e-4


class TestDropUnobtainableDemandItems:
    def test_fixed_point_reachability(self, make_calculator):
        calc = make_calculator({})
        activities = [
            # Producible from coins
            {'inputs': {1: 1}, 'outputs': {1000: 1}},
            # Producible from the previous output
            {'inputs': {1000: 1}, 'outputs': {1001: 1}},
            # Requires an item nothing supplies
            {'inputs': {424242: 1}, 'outputs': {1002: 1}},
        ]
        demand = {item_id: {'rate_per_day': 1} for item_id in [1000, 1001, 1002, 1003]}
        result = calc._drop_unobtainable_demand_items(demand, activities, initial_supply={})
        assert set(result) == {1000, 1001}

    def test_initial_supply_counts_as_obtainable(self, make_calculator):
        calc = make_calculator({})
        demand = {1003: {'rate_per_day': 1}}
        result = calc._drop_unobtainable_demand_items(demand, [], initial_supply={1003: 5})
        assert set(result) == {1003}

    def test_no_demand_passthrough(self, make_calculator):
        calc = make_calculator({})
        assert calc._drop_unobtainable_demand_items({}, [], initial_supply={}) == {}


class TestHardFloorNormalization:
    def test_round_up_and_drop_non_positive(self, make_calculator):
        calc = make_calculator({})
        result = calc._build_planner_hard_floor_items({'2700': 2.3, 2800: 0, 1000: -1, 1001: 4})
        assert result == {2700: 3, 1001: 4}

    def test_none_input(self, make_calculator):
        calc = make_calculator({})
        assert calc._build_planner_hard_floor_items(None) == {}


class TestRanchSecondProduct:
    @staticmethod
    def get_recipe_activity(calc, recipe_id):
        problem = calc._build_production_problem()
        return next(
            activity for activity in problem['activities']
            if activity['kind'] == 'recipe' and activity['id'] == recipe_id
        )

    def test_second_product_amortized_over_three_batches(self, make_calculator):
        # 400001 unlocks ranch second products, 2 chicken levels triple a batch
        calc = make_calculator({400001: True, 410301: True, 410302: True})
        eggs = self.get_recipe_activity(calc, 101013)
        assert eggs['inputs'] == {3000: 2 * 3}
        assert eggs['outputs'][2601] == pytest.approx(5 * 3)
        # 4 poultry per drop, one drop every 3 batches
        assert eggs['outputs'][2602] == pytest.approx(4 * 3 / 3)

    def test_no_second_product_without_technology(self, make_calculator):
        calc = make_calculator({410301: True, 410302: True})
        eggs = self.get_recipe_activity(calc, 101013)
        assert 2602 not in eggs['outputs']


class TestProblemBuilding:
    STONE_BALANCE = ('item_balance', 2700)

    def test_build_does_not_solve_and_matches_solve(self, make_calculator):
        kwargs = {'task_target_items': {2700: 100}, 'task_target_period': 20}
        solved = make_calculator({})
        solved.solve_production_plan(**kwargs)
        builder = make_calculator({})
        problem = builder.build_production_problem(**kwargs)
        assert builder.lp_status is None
        assert builder.production_plan == {}
        row = problem['constraint_labels'].index(('demand', 2700))
        assert problem['constraints'].lb[row] == pytest.approx(5.0)

        result = milp(problem['c'], constraints=problem['constraints'], bounds=problem['bounds'])
        builder._apply_production_lp_result(result, problem)
        assert builder.lp_success
        assert builder.production_plan == pytest.approx(solved.production_plan)
        assert builder.net_items == pytest.approx(solved.net_items)
        assert builder.demand_items == solved.demand_items

    def test_extend_appends_without_touching_original(self, make_calculator):
        problem = make_calculator({}).build_production_problem()
        n = len(problem['c'])
        m = problem['constraints'].A.shape[0]
        original_a = problem['constraints'].A.copy()
        original_labels = list(problem['constraint_labels'])

        extended = extend_problem(problem, columns=[
            {'label': 'extra_stone', 'cost': -1, 'ub': 10, 'rows': {self.STONE_BALANCE: 1}},
            {'label': 'allow', 'ub': 1, 'integer': True},
        ], rows=[
            {'label': 'gate', 'columns': {'extra_stone': 1, 'allow': -10}, 'ub': 0},
        ])
        assert extended['constraints'].A.shape == (m + 1, n + 2)
        assert extended['constraint_labels'] == original_labels + ['gate']
        assert extended['column_labels'] == {'extra_stone': n, 'allow': n + 1}
        assert extended['constraints'].A[original_labels.index(self.STONE_BALANCE), n] == 1
        assert list(extended['constraints'].A[m, n:]) == [1, -10]
        assert list(extended['c'][n:]) == [-1, 0]
        assert list(extended['integrality']) == [0] * n + [0, 1]
        assert list(extended['bounds'].ub[n:]) == [10, 1]
        np.testing.assert_array_equal(extended['constraints'].A[:m, :n], original_a)
        # The input problem is not modified
        assert problem['constraints'].A.shape == (m, n)
        np.testing.assert_array_equal(problem['constraints'].A, original_a)
        assert problem['constraint_labels'] == original_labels
        assert 'column_labels' not in problem and 'integrality' not in problem

        twice = extend_problem(extended, columns=[{'label': 'more', 'integer': True}],
                               rows=[{'label': 'cap', 'columns': {'more': 1, n: 1}, 'ub': 5}])
        assert twice['column_labels'] == {'extra_stone': n, 'allow': n + 1, 'more': n + 2}
        assert list(twice['integrality'][n:]) == [0, 1, 1]
        assert twice['constraints'].A[m + 1, n] == 1

    def test_column_on_balance_row_acts_as_supply(self, make_calculator):
        problem = make_calculator({}).build_production_problem()
        extended = extend_problem(problem, columns=[
            {'label': 'extra_stone', 'ub': 10, 'rows': {self.STONE_BALANCE: 1}},
            {'label': 'allow', 'cost': 1e-3, 'ub': 1, 'integer': True},
        ], rows=[
            {'label': 'gate', 'columns': {'extra_stone': 1, 'allow': -10}, 'ub': 0},
        ])
        result = milp(extended['c'], integrality=extended['integrality'],
                      constraints=extended['constraints'], bounds=extended['bounds'])
        assert result.success
        stone = result.x[extended['column_labels']['extra_stone']]
        allow = result.x[extended['column_labels']['allow']]
        # Extra stone is worth at least its pt_num, more than the gate cost
        assert allow == pytest.approx(1)
        assert stone == pytest.approx(10)

        # Same optimum as raising the stone supply of the original problem by 10
        row = problem['constraint_labels'].index(self.STONE_BALANCE)
        lb = problem['constraints'].lb.copy()
        ub = problem['constraints'].ub.copy()
        lb[row] -= stone
        ub[row] -= stone
        shifted = milp(problem['c'], constraints=LinearConstraint(problem['constraints'].A, lb, ub),
                       bounds=problem['bounds'])
        assert shifted.fun == pytest.approx(result.fun - 1e-3 * allow, abs=1e-6)
        base = milp(problem['c'], constraints=problem['constraints'], bounds=problem['bounds'])
        assert base.fun - shifted.fun >= 10 * DIC_ISLAND_ITEM[2700]['pt_num'] - EPS

    def test_extend_rejects_bad_labels(self, make_calculator):
        problem = make_calculator({}).build_production_problem()
        with pytest.raises(ValueError):
            extend_problem(problem, rows=[{'label': self.STONE_BALANCE, 'columns': {}}])
        with pytest.raises(ValueError):
            extend_problem(problem, columns=[{'label': 3}])
        with pytest.raises(ValueError):
            extend_problem(problem, columns=[{'label': 'a'}, {'label': 'a'}])
        with pytest.raises(KeyError):
            extend_problem(problem, columns=[{'label': 'a', 'rows': {('item_balance', -1): 1}}])
