from types import SimpleNamespace

import pytest

from module.island_handler.production_plan_calculator import ProductionPlanCalculator


FLOUR_ACTIVITY = {'kind': 'shop', 'id': 103004, 'group': None, 'workload': 0,
                  'inputs': {2000: 6}, 'outputs': {3004: 1}}
COW_FEED_ACTIVITY = {'kind': 'shop', 'id': 103002, 'group': None, 'workload': 0,
                     'inputs': {2008: 30}, 'outputs': {3002: 10}}


class TestConversionIdleRedirect:
    def test_pt_neutral_shop_ids(self):
        # Flour and chicken/pig feed keep PT, cow/sheep feed gain PT
        assert ProductionPlanCalculator.PT_NEUTRAL_SHOP_IDS == {103000, 103001, 103004}

    def test_idle_flour_exported_as_wheat(self, make_calculator):
        calc = make_calculator({})
        calc.net_idle_accumulating_items = {3004: 10, 2000: 5}
        # 12 flour bought, 2 of them consumed, 10 left idle
        ratios = calc._redirect_conversion_idle_accumulating_items([12], [FLOUR_ACTIVITY])
        assert calc.net_idle_accumulating_items == {2000: pytest.approx(5 + 10 * 6)}
        assert ratios == {0: pytest.approx(10 / 12)}

    def test_pt_gaining_shop_conversion_kept(self, make_calculator):
        calc = make_calculator({})
        calc.net_idle_accumulating_items = {3002: 10}
        ratios = calc._redirect_conversion_idle_accumulating_items([1], [COW_FEED_ACTIVITY])
        assert calc.net_idle_accumulating_items == {3002: 10}
        assert ratios == {}

    def test_total_pt_counts_idle_fish_meat(self, make_calculator):
        calc = make_calculator({})
        # Exchange 1 yellowfin tuna per day into 18 saltwater fish meat, left idle
        exchange = {'kind': 'exchange', 'id': 206, 'group': None, 'workload': 0,
                    'inputs': {5107: 1}, 'outputs': {2522: 18}}
        problem = {
            'activities': [exchange], 'sale_entries': [], 'item_index': {5107: 0, 2522: 1},
            'end_offset': 1, 'group_slots': {}, 'wild_gather_plan': {}, 'mining_supply_plan': {},
            'logging_supply_plan': {}, 'demand_items': {}, 'hard_floor_items': {},
            'task_target_items': {}, 'stuck_season_order_id': 0, 'stuck_season_order_items': {},
        }
        result = SimpleNamespace(status=0, success=True, message='', x=[1, 0, 18])
        calc._apply_production_lp_result(result, problem)
        assert calc.idle_accumulating_items_per_day == {5107: 1}
        assert calc.total_pt == pytest.approx(18 * 48)

    def test_idle_conversion_share_needs_no_buffer(self, make_calculator):
        calc = make_calculator({})
        kwargs = dict(solution=[12], activities=[FLOUR_ACTIVITY], sale_entries=[], activity_count=1)
        assert calc._calculate_product_daily_buffer_items(**kwargs) == {2000: 72}
        # 10 of 12 flour left idle, only the wheat of 2 flour is consumed daily
        assert calc._calculate_product_daily_buffer_items(**kwargs, idle_ratios={0: 10 / 12}) == {2000: 12}
