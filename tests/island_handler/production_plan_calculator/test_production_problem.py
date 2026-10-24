import pytest

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
