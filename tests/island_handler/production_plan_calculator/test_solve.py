from datetime import datetime, timedelta

import pytest
from yaml import safe_load

import module.config.server as server
from module.island.data import DIC_ISLAND_ACTIVITY

EPS = 1e-4


class TestSolveBaseTechnology:
    def test_initial_state_before_solve(self, make_calculator):
        calc = make_calculator({})
        assert calc.lp_success is False
        assert calc.production_plan == {}
        assert calc.demand_items == {}

    def test_scalar_task_target_requires_planning_period(self, make_calculator):
        calc = make_calculator({})
        with pytest.raises(ValueError, match='No planning period was provided'):
            calc.solve_production_plan(task_target_items={2700: 100})

    def test_scalar_stuck_order_requires_planning_period(self, make_calculator):
        calc = make_calculator({})
        with pytest.raises(ValueError, match='No planning period was provided'):
            calc.solve_production_plan(
                stuck_season_order_id=100015,
                current_time=datetime(1970, 1, 1),
            )

    def test_stuck_order_uses_period_from_injected_current_time(self, make_calculator):
        activity = DIC_ISLAND_ACTIVITY[990023]
        end = datetime.strptime(activity['end_time'][server.server], '%Y-%m-%d %H:%M:%S')
        calc = make_calculator({})
        calc.solve_production_plan(
            stuck_season_order_id=100015,
            current_time=end - timedelta(days=20),
        )
        assert calc.stuck_season_order_id == 100060
        assert calc.stuck_season_order_items[4011]['rate_per_day'] == pytest.approx(0.25)
        assert calc.stuck_season_order_items[4013]['rate_per_day'] == pytest.approx(0.25)

    def test_demand_satisfied_and_invalid_stuck_order_ignored(self, make_calculator):
        calc = make_calculator({})
        # 2700 (stone) is passively supplied by mining: 9 sites x 8/day
        calc.solve_production_plan(
            task_target_items={2700: 100},
            task_target_period=20,
            stuck_season_order_id='abc',
        )
        assert calc.lp_success
        assert calc.demand_items[2700]['rate_per_day'] == pytest.approx(5.0)
        assert calc.net_items.get(2700, 0) >= 5 - EPS
        assert calc.mining_supply_plan == {2700: 72}
        assert calc.logging_supply_plan == {2800: 72}
        # Invalid stuck order id normalizes to no stuck demand
        assert calc.stuck_season_order_id == 0
        assert calc.stuck_season_order_items == {}

    def test_unobtainable_demand_dropped_keeps_plan_feasible(self, make_calculator):
        calc = make_calculator({})
        # 3054 (clock) needs locked manufacturing technology and has no
        # shop/exchange source, so its demand must be dropped, not kill the LP.
        calc.solve_production_plan(task_target_items={3054: 5}, task_target_period=10)
        assert calc.lp_success
        assert 3054 not in calc.demand_items

    def test_impossible_demand_fails_with_empty_plans(self, make_calculator):
        calc = make_calculator({})
        calc.solve_production_plan(
            task_target_items={2700: 10 ** 9},
            task_target_period=10,
        )
        assert not calc.lp_success
        assert calc.production_plan == {}
        assert calc.sell_plan == {}
        # Inputs are still recorded for reporting
        assert 2700 in calc.demand_items
        failure_text = '\n'.join(calc.failure_diagnostics)
        assert f'Demand bottleneck: {calc._item_name(2700)} (2700)' in failure_text
        assert 'mining x72/day' in failure_text
        report = calc.format_solved_production_plan()
        assert '[restaurant_config]' in report
        assert '[planning_failure]' in report

    def test_impossible_recipe_demand_reports_saturated_production(
            self, make_calculator, all_unlocked_technology):
        calc = make_calculator(
            all_unlocked_technology,
            restaurant_settings={
                601: {'grade': 'gold', 'waitress_slots': ('any', 'none')},
            },
        )
        calc.solve_production_plan(
            task_target_items={2000: 10 ** 6},
            task_target_period=10,
        )

        assert not calc.lp_success
        failure_text = '\n'.join(calc.failure_diagnostics)
        assert f'Demand bottleneck: {calc._item_name(2000)} (2000)' in failure_text
        assert 'Production bottleneck:' in failure_text
        assert f'{calc._recipe_name(101001)} (101001)' in failure_text
        assert 'Restaurant bottleneck:' in failure_text

    def test_ranch_bottleneck_reports_daily_product_throughput(self, make_calculator):
        calc = make_calculator({
            310101: True,
            420301: True,
            420302: True,
            500211: True,
            500212: True,
            540001: True,
        }, restaurant_settings={
            901: {'grade': 'bronze', 'waitress_slots': ('any', 'none')},
        })
        calc.solve_production_plan(
            task_target_items={3029: 250},
            task_target_period=10,
        )

        assert not calc.lp_success
        failure_text = '\n'.join(calc.failure_diagnostics)
        assert 'requires 25/day (250 in 10 day(s))' in failure_text
        assert '鲜肉 (101015) x12 batches/day -> 鲜肉 (2600) x96/day' in failure_text


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

    def test_conversion_output_not_exported_as_idle(self, all_tech_koi_solved):
        # Production cannot schedule flour, chicken/pig feed or fish meat
        idle = set(all_tech_koi_solved.idle_accumulating_items_per_day)
        assert not idle & {3000, 3001, 3004, 2521, 2522}

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
        for section in ['[restaurant_config]', '[production]', '[sell]', '[daily_buffer_items]']:
            assert section in text
        assert (
            '(601): grade=gold, waitress_slots=[Chao_Ho, none], enabled=True'
            in text
        )
        assert 'shelf_count=3, shelf_capacity=7, total_capacity=21/day, sales_bonus=10%' in text


class TestDailyBufferSafetyMargin:
    def test_margin_scales_buffer(self, margin_solved):
        calc0, calc1 = margin_solved
        assert calc0.lp_success and calc1.lp_success
        assert calc0.product_daily_buffer_items, 'expected buffer items to compare'
        # Margin does not change the LP itself, only export post-processing
        assert set(calc0.product_daily_buffer_items) == set(calc1.product_daily_buffer_items)
        for item_id, amount in calc0.product_daily_buffer_items.items():
            assert calc1.product_daily_buffer_items[item_id] >= amount

    def test_negative_margin_clamped(self, make_calculator):
        calc = make_calculator({}, daily_buffer_safety_margin=-5)
        assert calc.daily_buffer_safety_margin == 0
