"""Tests for the pure island production plan calculator.

Run with (pytest is not a repo dependency, install it yourself):
    pixi run python -m pytest tests/ -v
"""
from datetime import datetime, timedelta

import pytest
from yaml import safe_load

import module.config.server as server
from module.island.data import DIC_ISLAND_ACTIVITY, DIC_ISLAND_SEASON
from module.island_handler.production_plan_calculator import (
    ProductionPlanCalculator,
    get_current_activity_list,
)

EPS = 1e-4


class AllUnlockedTechnology(dict):
    """Technology status stub reporting every technology as unlocked."""

    def get(self, key, default=False):
        return True


def make_calculator(technology_status=None, **kwargs):
    if technology_status is None:
        technology_status = {}
    return ProductionPlanCalculator(technology_status, **kwargs)


@pytest.fixture(scope='module')
def all_tech_koi_solved():
    """All technology unlocked, Koi restaurant selling, profit floor 10."""
    calc = make_calculator(
        AllUnlockedTechnology(),
        restaurant_settings={601: {'grade': 'gold', 'waitress_slots': ('Chao_Ho', 'none')}},
        daily_profit_lower_limit=10,
    )
    calc.solve_production_plan()
    return calc


@pytest.fixture(scope='module')
def margin_solved():
    """Same all-tech problem solved with safety margin 0 and 1.0."""
    calc0 = make_calculator(AllUnlockedTechnology(), daily_buffer_safety_margin=0)
    calc0.solve_production_plan()
    calc1 = make_calculator(AllUnlockedTechnology(), daily_buffer_safety_margin=1.0)
    calc1.solve_production_plan()
    return calc0, calc1


class TestStaticHelpers:
    def test_get_quantity_from_grade(self):
        assert ProductionPlanCalculator.get_quantity_from_grade('bronze') == 2
        assert ProductionPlanCalculator.get_quantity_from_grade('silver') == 2
        assert ProductionPlanCalculator.get_quantity_from_grade('gold') == 3
        assert ProductionPlanCalculator.get_quantity_from_grade('diamond') == 4
        with pytest.raises(ValueError):
            ProductionPlanCalculator.get_quantity_from_grade('paper')

    def test_format_amount(self):
        fmt = ProductionPlanCalculator._format_amount
        assert fmt(3) == '3'
        assert fmt(3.0000000001) == '3'
        assert fmt(2.5) == '2.5'
        assert fmt(0.12345) == '0.123'
        assert fmt(0) == '0'

    def test_round_output_amount(self):
        rnd = ProductionPlanCalculator._round_output_amount
        assert rnd(2.9999999999) == 3.0
        assert rnd(2.3456) == 2.346
        assert rnd(0) == 0.0


class TestGetCurrentActivityList:
    def test_inside_season(self):
        season = next(iter(DIC_ISLAND_SEASON.values()))
        start = datetime.strptime(season['start_time'][server.server], '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(season['end_time'][server.server], '%Y-%m-%d %H:%M:%S')
        midpoint = start + (end - start) / 2
        assert get_current_activity_list(midpoint) == season['activity']

    def test_outside_all_seasons(self):
        assert get_current_activity_list(datetime(1970, 1, 1)) is None


class TestAnalyzeTechnologyStatus:
    def test_base_slots_with_empty_technology(self):
        calc = make_calculator({})
        # Slots available without any technology
        for slot in [9031, 9041, 9061, 9201, 9211]:
            assert calc.slot_available[slot], slot
        # Slots requiring technology
        for slot in [9001, 9011, 9021, 9032, 9042, 9062, 9203, 9212]:
            assert not calc.slot_available[slot], slot
        assert calc.ranch_level == {9031: 0, 9032: 0, 9033: 0, 9034: 0}
        assert not calc.mining_additional
        assert not calc.ranch_additional

    def test_technology_unlocks_slot_and_recipe(self):
        calc = make_calculator({310101: True, 410301: True, 410302: True, 500212: True})
        assert calc.slot_available[9001]
        assert not calc.slot_available[9002]
        assert calc.ranch_level[9031] == 2
        # 玉米 recipe gated by 500212
        assert calc.recipe_available[101002]
        # 牧草 recipe still locked
        assert not calc.recipe_available[101003]

    def test_recipe_available_defaults(self):
        calc = make_calculator({})
        # Ungated normal recipe defaults to available
        assert calc.recipe_available[101001]
        # Gated recipe defaults to locked
        assert not calc.recipe_available[101002]

    def test_wild_gather_availability(self):
        calc = make_calculator({})
        assert calc.wild_gather_available[1]
        # Gathers 5 and 6 are gated by technology
        assert not calc.wild_gather_available[5]
        assert not calc.wild_gather_available[6]
        # Activity gathers default to unavailable
        assert not calc.wild_gather_available[1001]
        calc = make_calculator({450301: True})
        assert calc.wild_gather_available[5]

    def test_activity_list_enables_activity_content(self):
        recipe_activity_id, recipe_ids = next(
            (activity_id, data['config_data'])
            for activity_id, data in DIC_ISLAND_ACTIVITY.items()
            if data['type'] == 5004 and data['config_data']
        )
        gather_activity_id, gather_ids = next(
            (activity_id, data['config_data'])
            for activity_id, data in DIC_ISLAND_ACTIVITY.items()
            if data['type'] == 5003 and data['config_data']
        )
        calc = make_calculator({}, activity_list=[recipe_activity_id, gather_activity_id])
        for recipe_id in recipe_ids:
            assert calc.recipe_available[recipe_id], recipe_id
        for gather_id in gather_ids:
            assert calc.wild_gather_available[gather_id], gather_id
        # Without the activity list they stay unavailable, unless the recipe
        # is also attached to an available slot's activity_formula
        calc = make_calculator({})
        assert not any(
            calc.recipe_available.get(recipe_id, False)
            for recipe_id in recipe_ids
            if recipe_id not in calc.available_slot_recipes
        )

    def test_place_efficiency_bonus(self):
        calc = make_calculator({220601: True}, place_efficiency={101: 0.05, 501: None})
        assert calc.place_efficiency_bonus[101] == 0.05
        assert calc.place_efficiency_bonus[401] == 0.05
        assert calc.place_efficiency_bonus[402] == 0
        # None from config falls back to 0
        assert calc.place_efficiency_bonus[501] == 0


class TestRestaurantSettings:
    def test_default_settings_disable_restaurants(self):
        calc = make_calculator({})
        for restaurant_id in calc.restaurant_enabled:
            assert not calc.restaurant_enabled[restaurant_id]
        assert calc.restaurant_capacity[601] == 5  # bronze
        assert calc.restaurant_quantity[601] == 2
        assert calc.restaurant_sales_bonus[601] == 0

    def test_waitress_effects(self):
        calc = make_calculator({}, restaurant_settings={
            601: {'grade': 'gold', 'waitress_slots': ('Chao_Ho', 'none')},
            603: {'grade': 'gold', 'waitress_slots': ('Prinz_Eugen', 'none')},
        })
        # Chao_Ho: +1 capacity, +10% sales
        assert calc.restaurant_capacity[601] == 7
        assert calc.restaurant_quantity[601] == 3
        assert calc.restaurant_sales_bonus[601] == pytest.approx(0.10)
        assert calc.restaurant_enabled[601]
        # Prinz_Eugen: +0 capacity, +10% sales
        assert calc.restaurant_capacity[603] == 6
        assert calc.restaurant_sales_bonus[603] == pytest.approx(0.10)


class TestDropUnobtainableDemandItems:
    def test_fixed_point_reachability(self):
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

    def test_initial_supply_counts_as_obtainable(self):
        calc = make_calculator({})
        demand = {1003: {'rate_per_day': 1}}
        result = calc._drop_unobtainable_demand_items(demand, [], initial_supply={1003: 5})
        assert set(result) == {1003}

    def test_no_demand_passthrough(self):
        calc = make_calculator({})
        assert calc._drop_unobtainable_demand_items({}, [], initial_supply={}) == {}


class TestHardFloorNormalization:
    def test_round_up_and_drop_non_positive(self):
        calc = make_calculator({})
        result = calc._build_planner_hard_floor_items({'2700': 2.3, 2800: 0, 1000: -1, 1001: 4})
        assert result == {2700: 3, 1001: 4}

    def test_none_input(self):
        calc = make_calculator({})
        assert calc._build_planner_hard_floor_items(None) == {}


class TestSolveBaseTechnology:
    def test_initial_state_before_solve(self):
        calc = make_calculator({})
        assert calc.lp_success is False
        assert calc.production_plan == {}
        assert calc.demand_items == {}

    def test_demand_satisfied_and_invalid_stuck_order_ignored(self):
        calc = make_calculator({})
        # 2700 (stone) is passively supplied by mining: 9 sites x 8/day
        calc.solve_production_plan(task_target_items={2700: 100}, stuck_season_order_id='abc')
        assert calc.lp_success
        # 100 over default 10-day period -> 10 per day
        assert calc.demand_items[2700]['rate_per_day'] == pytest.approx(10.0)
        assert calc.net_items.get(2700, 0) >= 10 - EPS
        assert calc.mining_supply_plan == {2700: 72}
        assert calc.logging_supply_plan == {2800: 72}
        # Invalid stuck order id normalizes to no stuck demand
        assert calc.stuck_season_order_id == 0
        assert calc.stuck_season_order_items == {}

    def test_unobtainable_demand_dropped_keeps_plan_feasible(self):
        calc = make_calculator({})
        # 3054 (clock) needs locked manufacturing technology and has no
        # shop/exchange source, so its demand must be dropped, not kill the LP.
        calc.solve_production_plan(task_target_items={3054: 5})
        assert calc.lp_success
        assert 3054 not in calc.demand_items

    def test_impossible_demand_fails_with_empty_plans(self):
        calc = make_calculator({})
        calc.solve_production_plan(task_target_items={2700: 10 ** 9})
        assert not calc.lp_success
        assert calc.production_plan == {}
        assert calc.sell_plan == {}
        # Inputs are still recorded for reporting
        assert 2700 in calc.demand_items


class TestSolveAllTechnology:
    def test_solve_succeeds(self, all_tech_koi_solved):
        calc = all_tech_koi_solved
        assert calc.lp_success
        assert len(calc.production_plan) > 0

    def test_profit_lower_limit_respected(self, all_tech_koi_solved):
        calc = all_tech_koi_solved
        assert calc.daily_profit >= 10 - EPS

    def test_sell_plan_respects_restaurant_limits(self, all_tech_koi_solved):
        calc = all_tech_koi_solved
        assert calc.sell_plan, 'expected the LP to sell dishes'
        # Only the enabled restaurant sells
        assert {slot for slot, _ in calc.sell_plan} == {601}
        # Per-dish amount capped by shelf capacity
        assert all(amount <= calc.restaurant_capacity[601] + EPS for amount in calc.sell_plan.values())
        # Total sales capped by quantity x capacity
        total_limit = calc.restaurant_quantity[601] * calc.restaurant_capacity[601]
        assert sum(calc.sell_plan.values()) <= total_limit + EPS

    def test_group_usage_within_capacity(self, all_tech_koi_solved):
        calc = all_tech_koi_solved
        assert calc.group_usage_summary
        for group, data in calc.group_usage_summary.items():
            assert data['hours_per_slot'] <= 24 + EPS, group

    def test_amounts_positive(self, all_tech_koi_solved):
        calc = all_tech_koi_solved
        for plan in (calc.production_plan, calc.shop_plan, calc.exchange_plan, calc.sell_plan):
            assert all(amount > 0 for amount in plan.values())

    def test_yaml_exports_parse(self, all_tech_koi_solved):
        calc = all_tech_koi_solved
        buffer_items = safe_load(calc.daily_buffer_items_to_yaml())
        assert isinstance(buffer_items, dict) and buffer_items
        assert all(isinstance(amount, int) and amount >= 1 for amount in buffer_items.values())
        idle_items = safe_load(calc.idle_accumulating_items_to_yaml())
        assert idle_items is None or isinstance(idle_items, dict)
        menus = calc.restaurant_menus_to_yaml()
        assert sorted(menus) == [601, 602, 603, 604, 901]
        koi_menu = safe_load(menus[601])
        assert isinstance(koi_menu, dict) and koi_menu

    def test_format_solved_production_plan(self, all_tech_koi_solved):
        text = all_tech_koi_solved.format_solved_production_plan()
        assert 'LP success: True' in text
        for section in ['[production]', '[sell]', '[daily_buffer_items]']:
            assert section in text


class TestDailyBufferSafetyMargin:
    def test_margin_scales_buffer(self, margin_solved):
        calc0, calc1 = margin_solved
        assert calc0.lp_success and calc1.lp_success
        assert calc0.product_daily_buffer_items, 'expected buffer items to compare'
        # Margin does not change the LP itself, only export post-processing
        assert set(calc0.product_daily_buffer_items) == set(calc1.product_daily_buffer_items)
        for item_id, amount in calc0.product_daily_buffer_items.items():
            assert calc1.product_daily_buffer_items[item_id] >= amount

    def test_negative_margin_clamped(self):
        calc = make_calculator({}, daily_buffer_safety_margin=-5)
        assert calc.daily_buffer_safety_margin == 0
