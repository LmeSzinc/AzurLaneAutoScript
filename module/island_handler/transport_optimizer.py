"""Choose island transport commissions to submit, valued against the production plan.

Pure computation like production_plan_calculator: no config or device
dependencies, every input is passed in explicitly and every result is stored
as a plain attribute on TransportOptimizer.

Of the visible commissions, at most max_commissions (3 by default) can be
submitted. Each gets a 0-1 variable y_p in one MILP built on the problem from
ProductionPlanCalculator.build_production_problem. Choosing a commission adds
its change to stock d_p, claimed rewards and loading coins minus submitted
items, to the item balance rows, amortized over amortize_hours (12 by default)
of production output:

    max  H * V(sum_p d_p * y_p / H) + sum_p outside_p * y_p
    s.t. sum_p y_p <= max_commissions
         sum_p submitted_p,i * y_p <= max(effective_stock_i, 0)

The stock constraint is omitted when effective_stock is None, to value jobs
worth preserving for later rather than jobs that can be submitted now.

V is the production optimum in PT per day with supply raised by its argument,
H = amortize_hours / 24 day. Production is re-optimized in the same solve, so
commissions are valued together, including how they compete for items,
production capacity and the daily profit floor. Items without an item balance
row can't be produced or used by production, outside_p values them linearly at
pt_num.

Swapping a sub-commission into a primary slot makes it submittable and discards
the commission that was there, so any max_commissions of the visible
commissions can be submitted when that many primary slots are ready.
"""
from collections import defaultdict

from module.island.data import DIC_ISLAND_ITEM
from module.island_handler.milp import milp
from module.island_handler.production_plan_calculator import extend_problem
from module.logger import logger

# pg.island_set.order_ship_award_coefficient = {1, 25, 0}, loading an entry pays
# floor(order_price * count * 25 / 100) of item 1, development funds
LOADING_AWARD_ITEM = 1
LOADING_AWARD_PERCENT = 25


class TransportCommission:
    def __init__(self, submissions, rewards=None, name=''):
        """
        Args:
            submissions (list[tuple[int, int]]): (item_id, count) entries to submit.
            rewards (dict[int, int]): {item_id: count} claimed after submitting,
                loading coins excluded.
            name (str): For logging.
        """
        self.submissions = [(int(item_id), int(count)) for item_id, count in submissions]
        self.rewards = {int(item_id): count for item_id, count in (rewards or {}).items()}
        self.name = name

    def __repr__(self):
        return f'TransportCommission({self.name}, {self.submissions}, rewards={self.rewards})'

    @property
    def submitted_items(self):
        """{item_id: total count submitted}"""
        submitted = defaultdict(int)
        for item_id, count in self.submissions:
            submitted[item_id] += count
        return dict(submitted)

    def stock_change(self):
        """
        Returns:
            dict: {item_id: change to stock} of submitting and claiming. Loading
                coins are floored per entry, as the game does.
        """
        change = defaultdict(int)
        for item_id, count in self.submissions:
            change[item_id] -= count
            price = DIC_ISLAND_ITEM[item_id]['order_price']
            change[LOADING_AWARD_ITEM] += price * count * LOADING_AWARD_PERCENT // 100
        for item_id, count in self.rewards.items():
            change[item_id] += count
        return dict(change)


class TransportOptimizer:
    MAX_COMMISSIONS = 3
    AMORTIZE_HOURS = 12
    # The objective holds the whole production value, ~1e5 PT/day, so the
    # default relative gap of 1e-4 would accept choices ~10 PT/day worse.
    MILP_OPTIONS = {'mip_rel_gap': 0}
    GAIN_EPSILON = 1e-6

    def __init__(self, problem, max_commissions=MAX_COMMISSIONS, amortize_hours=AMORTIZE_HOURS):
        """
        Args:
            problem (dict): From ProductionPlanCalculator.build_production_problem,
                not modified.
            max_commissions (int): Maximum number of commissions to submit.
            amortize_hours (float): Hours of production output the changes to
                stock are amortized over.
        """
        self.problem = problem
        self.max_commissions = max_commissions
        self.amortize_hours = amortize_hours
        self.balance_items = {key for kind, key in problem['constraint_labels'] if kind == 'item_balance'}
        result = milp(problem['c'], constraints=problem['constraints'], bounds=problem['bounds'])
        # Production optimum without commissions, PT/day, None if infeasible
        self.base_value = -result.fun if result.success else None

        self.chosen = []
        self.gain = 0.
        self.message = ''
        self.success = False

    def select(self, commissions, effective_stock):
        """
        Choose up to max_commissions commissions with the highest total gain.

        Args:
            commissions (list[TransportCommission]): Visible commissions.
            effective_stock (dict | None): {item_id: effective stock at the check time},
                as get_order_effective_stock(stock, hard_floor, reserve).
                Items missing have none. None omits the immediate stock limit.

        Returns:
            list[int]: Indices of chosen commissions, also stored in self.chosen,
                with the extra PT over the amortization window in self.gain.
        """
        self.chosen = []
        self.gain = 0.
        self.success = False
        if self.base_value is None:
            self.message = 'Production problem is infeasible, transport commissions cannot be valued'
            logger.warning(self.message)
            return self.chosen
        if not commissions:
            self.message = 'No transport commission'
            self.success = True
            return self.chosen

        problem = self._build_selection_problem(commissions, effective_stock)
        result = milp(problem['c'], integrality=problem['integrality'], bounds=problem['bounds'],
                      constraints=problem['constraints'], options=dict(self.MILP_OPTIONS))
        if not result.success:
            self.message = f'Transport selection failed: {result.message}'
            logger.warning(self.message)
            return self.chosen

        self.success = True
        days = self.amortize_hours / 24
        gain = days * (-result.fun - self.base_value)
        if gain > self.GAIN_EPSILON:
            self.chosen = [
                index for index in range(len(commissions))
                if result.x[problem['column_labels'][('commission', index)]] > 0.5
            ]
            self.gain = gain
        names = ', '.join(commissions[index].name or str(index) for index in self.chosen) or 'none'
        self.message = (f'Transport commissions chosen: {names}, '
                        f'gain {self.gain:.1f} PT over {self.amortize_hours}h')
        logger.info(self.message)
        return self.chosen

    def _build_selection_problem(self, commissions, effective_stock):
        days = self.amortize_hours / 24
        columns = []
        submitted = defaultdict(dict)
        for index, commission in enumerate(commissions):
            label = ('commission', index)
            rows = {}
            outside = 0.
            for item_id, amount in commission.stock_change().items():
                if item_id in self.balance_items:
                    rows[('item_balance', item_id)] = amount / days
                else:
                    outside += DIC_ISLAND_ITEM[item_id]['pt_num'] * amount
            columns.append({'label': label, 'cost': -outside / days, 'ub': 1, 'integer': True, 'rows': rows})
            for item_id, count in commission.submitted_items.items():
                submitted[item_id][label] = count

        rows = [{
            'label': ('commission_count',),
            'columns': {column['label']: 1 for column in columns},
            'ub': self.max_commissions,
        }]
        # Clamped at 0, negative effective stock covers nothing and choosing
        # no commission stays feasible
        if effective_stock is not None:
            for item_id, counts in sorted(submitted.items()):
                rows.append({
                    'label': ('effective_stock', item_id),
                    'columns': counts,
                    'ub': max(effective_stock.get(item_id, 0), 0),
                })
        return extend_problem(self.problem, columns=columns, rows=rows)
