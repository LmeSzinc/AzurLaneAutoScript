"""Tests for the pure island transport commission optimizer."""

import itertools
import math

import numpy as np
import pytest

import module.island_handler.transport_optimizer as transport_optimizer
from module.island.data import DIC_ISLAND_ITEM
from module.island_handler.milp import LinearConstraint, milp
from module.island_handler.production_plan_calculator import ProductionPlanCalculator
from module.island_handler.transport_optimizer import TransportCommission, TransportOptimizer

EPS = 1e-3
COIN = 1
IRON_ORE = 2703
CARROT = 2004


class AllUnlockedTechnology(dict):
    """Technology status stub reporting every technology as unlocked."""

    def get(self, key, default=False):
        return True


@pytest.fixture(scope='module')
def low_tech_problem():
    """Base technology, no restaurant. Carrot and iron ore have no balance row."""
    return ProductionPlanCalculator({}).build_production_problem()


@pytest.fixture(scope='module')
def all_tech_problem():
    """All technology, Koi restaurant selling, profit floor 10. Every transport item has a balance row."""
    calc = ProductionPlanCalculator(
        AllUnlockedTechnology(),
        restaurant_settings={601: {'grade': 'gold', 'waitress_slots': ('Chao_Ho', 'none')}},
        daily_profit_lower_limit=10,
    )
    return calc.build_production_problem()


ALL_TECH_COMMISSIONS = [
    TransportCommission([(2005, 80), (2601, 30)], name='potato_eggs'),
    TransportCommission([(IRON_ORE, 50), (2012, 10)], name='iron_cotton'),
    TransportCommission([(2022, 50)], {COIN: 3000}, name='rubber'),
    TransportCommission([(5008, 20), (2015, 10)], {IRON_ORE: 20}, name='crab_lavender'),
    TransportCommission([(2521, 80)], name='fish_meat'),
    TransportCommission([(2600, 50), (2602, 80)], {2005: 50}, name='meat_poultry'),
]
LOW_TECH_COMMISSIONS = [
    TransportCommission([(CARROT, 30)], {IRON_ORE: 5}),
    TransportCommission([(2601, 20), (2602, 30)]),
    TransportCommission([(2009, 10)], {COIN: 500}),
    TransportCommission([(5001, 20)], {2016: 10}),
    TransportCommission([(2521, 10), (CARROT, 20)]),
    TransportCommission([(2016, 50)], {2602: 40}),
    TransportCommission([(5005, 10), (2601, 10)], {COIN: 200}),
    TransportCommission([(IRON_ORE, 10)]),
    TransportCommission([(2602, 10), (2009, 5)], {5001: 10}),
]
LOW_TECH_STOCK = {CARROT: 40, IRON_ORE: 10, 2601: 25, 2602: 40, 2009: 12, 5001: 30, 2521: 10, 2016: 50, 5005: 10}


# Transport screenshots of a JP account on 2026-10-20 03:13 server time: the 3
# commission slots P1-P3 and the commission list 01-06. Production inputs are
# from that account's config, with no TaskTarget and no stuck season order.
JP_TECHNOLOGIES = (
    210101, 210102, 210103, 210104, 210201, 210202, 210203, 210401, 210501, 210502,
    210601, 220101, 220102, 220103, 220104, 220201, 220202, 220203, 220204, 220401,
    220501, 220502, 220601, 310001, 310101, 310102, 310103, 310104, 310201, 310202,
    310301, 310302, 310303, 310304, 310305, 310306, 310307, 310308, 310309, 320101,
    320102, 320201, 320202, 320203, 320204, 320205, 320206, 320301, 320302, 320303,
    320304, 330101, 330102, 330103, 330104, 330201, 330301, 330302, 330303, 400001,
    410301, 410302, 410303, 410304, 410305, 420301, 420302, 420303, 420304, 430301,
    430302, 430303, 430304, 440301, 440302, 440303, 440304, 450301, 450302, 460001,
    460002, 460101, 460102, 460201, 460202, 460203, 460204, 460205, 460206, 460301,
    460302, 500001, 500211, 500212, 500213, 500214, 500215, 500231, 500232, 500233,
    500234, 500235, 500236, 510101, 510201, 510202, 510203, 510204, 520001, 520101,
    520201, 520202, 520203, 520204, 520205, 530001, 530101, 530202, 530203, 530204,
    530205, 530206, 540001, 540101, 540201, 540202, 540204, 540205, 550201, 550202,
    550203, 550204, 610101, 610102, 610401, 610402, 610403, 620101, 630101, 630201,
    630202, 630203, 630204, 630205, 640001, 640101, 640201, 640202, 640203, 640204,
    640205, 650001, 650101, 650201, 650202, 650203, 660001, 660101, 660201, 660202,
    660203, 660204, 660205, 660206,
)
JP_ACTIVITIES = [990022, 990023, 990024, 990025]
SCREENSHOT_COMMISSIONS = [
    # Onion, Freshwater Fish Meat, Freshwater Shrimp -> Saltwater Fish Meat, Potato, Sulfur
    TransportCommission([(2007, 8), (2521, 10), (5005, 9)], {2522: 7, 2005: 28, 2704: 1}, name='P1'),
    # Sea Cucumber -> Crayfish, Premium Wood
    TransportCommission([(5108, 4)], {5006: 25, 2802: 4}, name='P2'),
    # Banana, Copper Ore, Poultry -> Eggs, Cotton, Rubber
    TransportCommission([(2018, 36), (2701, 9), (2602, 48)], {2601: 39, 2012: 20, 2022: 3}, name='P3'),
    # Premium Wood -> Lavender, Workable Wood
    TransportCommission([(2802, 13)], {2015: 8, 2801: 18}, name='01'),
    # Freshwater Fish Meat, Milk -> Citrus Fruit, Saltwater Fish Meat
    TransportCommission([(2521, 8), (2603, 24)], {2017: 23, 2522: 8}, name='02'),
    # Apple, Fresh Meat -> Wool, Strawberries
    TransportCommission([(2016, 32), (2600, 16)], {2605: 4, 2011: 44}, name='03'),
    # Iron Ore, Apple, Saltwater Fish Meat -> Eggs, Workable Wood
    TransportCommission([(2703, 11), (2016, 38), (2522, 2)], {2601: 44, 2801: 18}, name='04'),
    # Onion -> Milk, Cotton
    TransportCommission([(2007, 19)], {2603: 10, 2012: 35}, name='05'),
    # Potato, Premium Wood -> Milk, Flax, Pelt
    TransportCommission([(2005, 47), (2802, 9)], {2603: 21, 2010: 13, 2604: 10}, name='06'),
]
# Owned counts on screen. The config has no hard floor or menu reserve on these
# items, so they are the effective stock as well.
SCREENSHOT_STOCK = {
    2007: 90, 2521: 0, 5005: 10, 5108: 0, 2018: 143, 2701: 105, 2602: 1,
    2802: 101, 2603: 0, 2016: 66, 2600: 0, 2703: 95, 2522: 6186, 2005: 460427,
}


@pytest.fixture(scope='module')
def jp_problem():
    calc = ProductionPlanCalculator(
        {technology_id: True for technology_id in JP_TECHNOLOGIES},
        activity_list=JP_ACTIVITIES,
        place_efficiency={101: 0.12, 501: 0.12, 502: 0.12},
        restaurant_settings={
            601: {'grade': 'diamond', 'waitress_slots': ('Chao_Ho', 'any')},
            602: {'grade': 'diamond', 'waitress_slots': ('Cheshire', 'any')},
            603: {'grade': 'diamond', 'waitress_slots': ('Helena', 'Prinz_Eugen')},
            604: {'grade': 'diamond', 'waitress_slots': ('August_von_Parseval', 'Prinz_Eugen')},
            901: {'grade': 'diamond', 'waitress_slots': ('Cheshire', 'Belfast')},
        },
        daily_profit_lower_limit=80000,
    )
    return calc.build_production_problem()


def stock_change(commission):
    """Change to stock, independent of TransportCommission.stock_change."""
    change = {}
    for item_id, count in commission.submissions:
        change[item_id] = change.get(item_id, 0) - count
        coins = math.floor(DIC_ISLAND_ITEM[item_id]['order_price'] * count * 25 / 100)
        change[COIN] = change.get(COIN, 0) + coins
    for item_id, count in commission.rewards.items():
        change[item_id] = change.get(item_id, 0) + count
    return change


def value_over_window(problem, change, hours=12):
    """PT over the window with the change amortized as supply, shifting balance row bounds directly."""
    days = hours / 24
    rows = {key: row for row, (kind, key) in enumerate(problem['constraint_labels']) if kind == 'item_balance'}
    lb = problem['constraints'].lb.copy()
    ub = problem['constraints'].ub.copy()
    outside = 0.
    for item_id, amount in change.items():
        if item_id in rows:
            lb[rows[item_id]] -= amount / days
            ub[rows[item_id]] -= amount / days
        else:
            outside += DIC_ISLAND_ITEM[item_id]['pt_num'] * amount
    result = milp(problem['c'], constraints=LinearConstraint(problem['constraints'].A, lb, ub),
                  bounds=problem['bounds'])
    if not result.success:
        return -np.inf
    return -result.fun * days + outside


def total_change(commissions, chosen):
    change = {}
    for index in chosen:
        for item_id, amount in stock_change(commissions[index]).items():
            change[item_id] = change.get(item_id, 0) + amount
    return change


def brute_force(problem, commissions, effective_stock, max_count=3):
    """Best gain and choice over every allowed set of commissions."""
    base = value_over_window(problem, {})
    best, best_chosen = 0., []
    for size in range(1, max_count + 1):
        for chosen in itertools.combinations(range(len(commissions)), size):
            used = {}
            for index in chosen:
                for item_id, count in commissions[index].submissions:
                    used[item_id] = used.get(item_id, 0) + count
            if any(count > max(effective_stock.get(item_id, 0), 0) for item_id, count in used.items()):
                continue
            gain = value_over_window(problem, total_change(commissions, chosen)) - base
            if gain > best + EPS:
                best, best_chosen = gain, list(chosen)
    return best, best_chosen


def loose_stock(commissions):
    stock = {}
    for commission in commissions:
        for item_id, count in commission.submissions:
            stock[item_id] = stock.get(item_id, 0) + count
    return stock


class TestTransportCommission:
    def test_loading_coins_floored_per_entry(self):
        price = DIC_ISLAND_ITEM[CARROT]['order_price']
        per_entry = math.floor(price * 25 / 100)
        # Precondition: flooring per entry differs from flooring the merged entry
        assert 2 * per_entry != math.floor(price * 2 * 25 / 100)
        commission = TransportCommission([(CARROT, 1), (CARROT, 1)], {CARROT: 5})
        assert commission.stock_change() == {CARROT: 3, COIN: 2 * per_entry}
        assert commission.submitted_items == {CARROT: 2}

    def test_rewards_add_to_loading_coins(self):
        commission = TransportCommission([(IRON_ORE, 10)], {COIN: 100, 2005: 7})
        assert commission.stock_change() == stock_change(commission)


class TestTransportOptimizer:
    def test_matches_brute_force_all_tech(self, all_tech_problem):
        shape = all_tech_problem['constraints'].A.shape
        stock = loose_stock(ALL_TECH_COMMISSIONS)
        optimizer = TransportOptimizer(all_tech_problem)
        chosen = optimizer.select(ALL_TECH_COMMISSIONS, stock)
        best, best_chosen = brute_force(all_tech_problem, ALL_TECH_COMMISSIONS, stock)
        assert best > 0
        assert optimizer.gain == pytest.approx(best, abs=EPS)
        assert 1 <= len(chosen) <= 3
        base = value_over_window(all_tech_problem, {})
        assert value_over_window(all_tech_problem, total_change(ALL_TECH_COMMISSIONS, chosen)) - base \
            == pytest.approx(optimizer.gain, abs=EPS)
        # The production problem is not modified
        assert all_tech_problem['constraints'].A.shape == shape
        assert 'column_labels' not in all_tech_problem

    def test_matches_brute_force_low_tech_tight_stock(self, low_tech_problem):
        optimizer = TransportOptimizer(low_tech_problem)
        chosen = optimizer.select(LOW_TECH_COMMISSIONS, LOW_TECH_STOCK)
        best, best_chosen = brute_force(low_tech_problem, LOW_TECH_COMMISSIONS, LOW_TECH_STOCK)
        assert best > 0
        assert optimizer.gain == pytest.approx(best, abs=EPS)
        assert sorted(chosen) == best_chosen

    def test_at_most_max_commissions(self, low_tech_problem):
        # Iron ore has no balance row here, rewards are worth exactly pt_num each
        commissions = [TransportCommission([], {IRON_ORE: amount}) for amount in (10, 50, 20, 40, 30)]
        optimizer = TransportOptimizer(low_tech_problem)
        assert sorted(optimizer.select(commissions, {})) == [1, 3, 4]
        assert optimizer.gain == pytest.approx(DIC_ISLAND_ITEM[IRON_ORE]['pt_num'] * 120, abs=EPS)
        optimizer = TransportOptimizer(low_tech_problem, max_commissions=1)
        assert optimizer.select(commissions, {}) == [1]

    def test_effective_stock_covers_total_submitted(self, low_tech_problem):
        commission = TransportCommission([(CARROT, 10)], {IRON_ORE: 5})
        optimizer = TransportOptimizer(low_tech_problem)
        assert optimizer.select([commission], {CARROT: 10}) == [0]
        assert optimizer.gain > 0
        # One short, missing and negative effective stock all exclude it
        for stock in ({CARROT: 9}, {}, {CARROT: -3}):
            assert optimizer.select([commission], stock) == []
            assert optimizer.gain == 0
        # Two commissions sharing an item are limited by their total
        assert len(optimizer.select([commission, commission], {CARROT: 19})) == 1
        assert len(optimizer.select([commission, commission], {CARROT: 20})) == 2

    def test_nothing_positive_chooses_none(self, all_tech_problem):
        # Loading coins are cheap here, unlike at low technology without coin income
        commissions = [TransportCommission([(5108, 30)]), TransportCommission([(5008, 20), (5108, 10)])]
        stock = loose_stock(commissions)
        best, _ = brute_force(all_tech_problem, commissions, stock)
        assert best == 0
        optimizer = TransportOptimizer(all_tech_problem)
        assert optimizer.select(commissions, stock) == []
        assert optimizer.gain == 0
        assert optimizer.success

    def test_parking_omits_only_immediate_stock_limit(self, low_tech_problem):
        optimizer = TransportOptimizer(low_tech_problem)
        assert optimizer.select(LOW_TECH_COMMISSIONS, {}) == []
        assert optimizer.success
        chosen = optimizer.select(LOW_TECH_COMMISSIONS, None)
        best, best_chosen = brute_force(low_tech_problem, LOW_TECH_COMMISSIONS, loose_stock(LOW_TECH_COMMISSIONS))
        assert sorted(chosen) == best_chosen
        assert optimizer.gain == pytest.approx(best, abs=EPS)
        assert optimizer.success

    def test_failed_selection_is_distinct_from_no_profitable_jobs(self, low_tech_problem, monkeypatch):
        optimizer = TransportOptimizer(low_tech_problem)
        assert optimizer.select(LOW_TECH_COMMISSIONS, LOW_TECH_STOCK)
        assert optimizer.success

        class FailedResult:
            success = False
            message = 'test solver failure'

        monkeypatch.setattr(transport_optimizer, 'milp', lambda *args, **kwargs: FailedResult())
        assert optimizer.select(LOW_TECH_COMMISSIONS, LOW_TECH_STOCK) == []
        assert not optimizer.success
        assert optimizer.gain == 0

    def test_amortized_as_12_hours_of_output(self, all_tech_problem):
        # Production scaled to 12 hours with the change injected once gives the same gain
        optimizer = TransportOptimizer(all_tech_problem, max_commissions=1)
        chosen = optimizer.select(ALL_TECH_COMMISSIONS, loose_stock(ALL_TECH_COMMISSIONS))
        assert len(chosen) == 1
        half = dict(all_tech_problem)
        constraints = all_tech_problem['constraints']
        half['constraints'] = LinearConstraint(constraints.A, constraints.lb / 2, constraints.ub / 2)
        bounds = all_tech_problem['bounds']
        half['bounds'] = type(bounds)(bounds.lb / 2, bounds.ub / 2)
        change = total_change(ALL_TECH_COMMISSIONS, chosen)
        gain = value_over_window(half, change, hours=24) - value_over_window(half, {}, hours=24)
        assert gain == pytest.approx(optimizer.gain, abs=EPS)

    def test_infeasible_production_chooses_none(self):
        # No restaurant earns coins, so a profit floor makes production infeasible
        problem = ProductionPlanCalculator({}, daily_profit_lower_limit=10).build_production_problem()
        optimizer = TransportOptimizer(problem)
        assert optimizer.base_value is None
        assert optimizer.select([TransportCommission([], {COIN: 1000})], {}) == []
        assert 'infeasible' in optimizer.message
        assert not optimizer.success

    def test_no_commission(self, low_tech_problem):
        optimizer = TransportOptimizer(low_tech_problem)
        assert optimizer.select([], {}) == []
        assert optimizer.gain == 0
        assert optimizer.success


class TestScreenshotCommissions:
    def test_production_reproduced(self, jp_problem):
        assert TransportOptimizer(jp_problem).base_value == pytest.approx(112362.193115, abs=EPS)

    def test_choice(self, jp_problem):
        # P1, P2, P3, 02 and 03 are short of stock, 04 gains least of the rest
        optimizer = TransportOptimizer(jp_problem)
        chosen = optimizer.select(SCREENSHOT_COMMISSIONS, SCREENSHOT_STOCK)
        assert [SCREENSHOT_COMMISSIONS[index].name for index in chosen] == ['01', '05', '06']
        assert optimizer.gain == pytest.approx(2599.2, abs=0.1)

    def test_choice_without_stock_limit(self, jp_problem):
        optimizer = TransportOptimizer(jp_problem)
        chosen = optimizer.select(SCREENSHOT_COMMISSIONS, None)
        assert [SCREENSHOT_COMMISSIONS[index].name for index in chosen] == ['03', '05', '06']
        assert optimizer.gain == pytest.approx(3300.8, abs=0.1)
