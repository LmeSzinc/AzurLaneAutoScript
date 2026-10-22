"""Backport of the HiGHS interface of SciPy for the pinned SciPy 1.4.1.

Later SciPy versions solve `milp` through
`scipy.optimize._highspy._highs_wrapper._highs_wrapper`. SciPy 1.4.1 does not
ship HiGHS, so this module provides `_highs_wrapper` with the same arguments
and results, solving by branch and bound over LP relaxations from linprog of
SciPy 1.4.1. module.island_handler.milp ports `milp` on top of it.

Differences from SciPy with HiGHS:
- No MIP presolve, cutting planes or primal heuristics, so it is meant for
  small problems. `mip_node_count` counts the LP relaxations solved, and
  iteration counts are those of linprog.
- Dual values are not computed, results have no `lambda` and `marg_bnds`.
- HiGHS options other than those in HIGHS_OPTION_DEFAULTS have no effect if
  in HIGHS_OPTIONS_IGNORED, and are reported as unrecognized otherwise.
  Option values are not range checked.
"""
import heapq
import itertools
import time
import warnings

import numpy as np
import scipy.sparse as sps
from scipy.optimize import OptimizeWarning
from scipy.optimize import linprog as _linprog


class HighsModelStatus:
    """Model status codes of HiGHS"""
    kNotset = 0
    kLoadError = 1
    kModelError = 2
    kPresolveError = 3
    kSolveError = 4
    kPostsolveError = 5
    kModelEmpty = 6
    kOptimal = 7
    kInfeasible = 8
    kUnboundedOrInfeasible = 9
    kUnbounded = 10
    kObjectiveBound = 11
    kObjectiveTarget = 12
    kTimeLimit = 13
    kIterationLimit = 14
    kUnknown = 15
    kSolutionLimit = 16
    kInterrupt = 17
    kMemoryLimit = 18


# HiGHS modelStatusToString() of the statuses given here
MODEL_STATUS_STRING = {
    HighsModelStatus.kModelError: 'Model error',
    HighsModelStatus.kSolveError: 'Solve error',
    HighsModelStatus.kOptimal: 'Optimal',
    HighsModelStatus.kInfeasible: 'Infeasible',
    HighsModelStatus.kUnboundedOrInfeasible: 'Primal infeasible or unbounded',
    HighsModelStatus.kUnbounded: 'Unbounded',
    HighsModelStatus.kTimeLimit: 'Time limit reached',
    HighsModelStatus.kIterationLimit: 'Iteration limit reached',
    HighsModelStatus.kSolutionLimit: 'Solution limit reached',
}
# HiGHS options that take effect here, and their HiGHS defaults
HIGHS_OPTION_DEFAULTS = {
    'presolve': True,
    'time_limit': np.inf,
    'mip_max_nodes': None,
    'mip_rel_gap': 1e-4,
    'mip_abs_gap': 1e-6,
    'mip_feasibility_tolerance': 1e-6,
    'log_to_console': True,
    'output_flag': True,
    'simplex_iteration_limit': None,
    'ipm_iteration_limit': None,
}
# Valid HiGHS options that have no effect here
HIGHS_OPTIONS_IGNORED = {
    'solver', 'highs_debug_level', 'dual_feasibility_tolerance', 'primal_feasibility_tolerance',
    'ipm_optimality_tolerance', 'simplex_dual_edge_weight_strategy', 'simplex_strategy',
}
HIGHS_BOOL_OPTIONS = {'presolve', 'log_to_console', 'output_flag'}
# linprog methods of SciPy 1.4.1 and their extra options, tried in order until one gives
# a definite answer. Revised simplex comes first because vertex solutions are integral
# more often. Autoscale retries handle relaxations that are numerically difficult unscaled.
LP_ATTEMPTS = (
    ('revised simplex', {}),
    ('revised simplex', {'autoscale': True}),
    ('interior-point', {}),
    ('simplex', {'autoscale': True}),
)


def _highs_to_scipy_status_message(highs_status, highs_message):
    """Converts HiGHS status number/message to SciPy status number/message"""
    scipy_statuses_messages = {
        None: (4, 'HiGHS did not provide a status code. '),
        HighsModelStatus.kNotset: (4, ''),
        HighsModelStatus.kLoadError: (4, ''),
        HighsModelStatus.kModelError: (2, ''),
        HighsModelStatus.kPresolveError: (4, ''),
        HighsModelStatus.kSolveError: (4, ''),
        HighsModelStatus.kPostsolveError: (4, ''),
        HighsModelStatus.kModelEmpty: (4, ''),
        HighsModelStatus.kObjectiveBound: (4, ''),
        HighsModelStatus.kObjectiveTarget: (4, ''),
        HighsModelStatus.kOptimal: (0, 'Optimization terminated successfully. '),
        HighsModelStatus.kTimeLimit: (1, 'Time limit reached. '),
        HighsModelStatus.kIterationLimit: (1, 'Iteration limit reached. '),
        HighsModelStatus.kInfeasible: (2, 'The problem is infeasible. '),
        HighsModelStatus.kUnbounded: (3, 'The problem is unbounded. '),
        HighsModelStatus.kUnboundedOrInfeasible: (4, 'The problem is unbounded '
                                                     'or infeasible. ')}
    unrecognized = (4, 'The HiGHS status code was not recognized. ')
    scipy_status, scipy_message = scipy_statuses_messages.get(highs_status, unrecognized)
    hstat = int(highs_status) if highs_status is not None else None
    scipy_message = f'{scipy_message}(HiGHS Status {hstat}: {highs_message})'
    return scipy_status, scipy_message


def _highs_options(options):
    """
    Returns:
        dict: HIGHS_OPTION_DEFAULTS updated by `options`, warning as SciPy's _highs_wrapper does.
    """
    parsed = dict(HIGHS_OPTION_DEFAULTS)
    for key, val in options.items():
        if val is None or key in ('sense',):
            continue
        if key not in HIGHS_OPTION_DEFAULTS and key not in HIGHS_OPTIONS_IGNORED:
            warnings.warn(f'Unrecognized options detected: {dict({key: val})}',
                          OptimizeWarning, stacklevel=3)
            continue
        if key in HIGHS_BOOL_OPTIONS and not isinstance(val, bool):
            warnings.warn(f'Option f"{key}" is "{val}", but only True or False is '
                          f'allowed. Using default.', OptimizeWarning, stacklevel=3)
            continue
        if key in HIGHS_OPTION_DEFAULTS:
            parsed[key] = val
    return parsed


class _LPRelaxation:
    """
    `min c @ x` subject to `lhs <= A @ x <= rhs`, solved by linprog of SciPy 1.4.1
    with variable bounds given per call.
    """

    def __init__(self, c, A, lhs, rhs, presolve=True, simplex_iteration_limit=None, ipm_iteration_limit=None):
        is_eq = lhs == rhs
        is_upper = ~is_eq & (rhs < np.inf)
        is_lower = ~is_eq & (lhs > -np.inf)
        self.c = c
        self.A_ub = np.vstack([A[is_upper], -A[is_lower]])
        self.b_ub = np.concatenate([rhs[is_upper], -lhs[is_lower]])
        self.A_eq = A[is_eq]
        self.b_eq = lhs[is_eq]
        if not self.b_ub.size:
            self.A_ub = self.b_ub = None
        if not self.b_eq.size:
            self.A_eq = self.b_eq = None
        self.presolve = presolve
        self.iteration_limit = {'simplex': simplex_iteration_limit, 'ipm': ipm_iteration_limit}
        self.nit = {'simplex': 0, 'ipm': 0}

    def solve(self, lb, ub):
        """
        Returns:
            tuple[str, np.ndarray, float, str]: status, x, fun, message.
                status is 'optimal', 'infeasible', 'unbounded', 'iteration_limit' or 'failed'.
        """
        bounds = list(zip(lb, ub))
        messages = []
        for method, options in LP_ATTEMPTS:
            kind = 'ipm' if method == 'interior-point' else 'simplex'
            limit = self.iteration_limit[kind]
            options = dict(options, presolve=self.presolve)
            if limit is not None:
                options['maxiter'] = max(limit - self.nit[kind], 0)
            try:
                with warnings.catch_warnings():
                    # Numerical warnings are common on degenerate relaxations,
                    # the returned status is checked instead.
                    warnings.simplefilter('ignore')
                    res = _linprog(self.c, A_ub=self.A_ub, b_ub=self.b_ub, A_eq=self.A_eq, b_eq=self.b_eq,
                                   bounds=bounds, method=method, options=options)
            except Exception as e:
                # SciPy 1.4.1 linprog raises instead of returning a status on some numerical failures
                messages.append(f'{method}: {e}')
                continue
            self.nit[kind] += res.nit
            if res.status == 0:
                return 'optimal', res.x, float(res.fun), res.message
            if res.status == 2:
                return 'infeasible', None, None, res.message
            if res.status == 3:
                return 'unbounded', None, None, res.message
            if res.status == 1 and limit is not None:
                return 'iteration_limit', None, None, res.message
            messages.append(f'{method}: {res.message}')
        return 'failed', None, None, ' '.join(messages)


def _branch_and_bound(lp, c, integrality, lb, ub, options):
    """
    Best-first branch and bound, diving into one child after each branching.

    Semi-continuous and semi-integer variables have domain {0} U [lb, ub].
    Until branched on, they are relaxed to the hull of that domain. Branching
    on them gives a child fixed at 0 and a child in [lb, ub], in which a
    semi-integer variable is a plain integer variable.

    Returns:
        dict: status, x, fun, mip_node_count, mip_dual_bound, mip_gap.
    """
    tol = options['mip_feasibility_tolerance']
    rel_gap = options['mip_rel_gap']
    abs_gap = options['mip_abs_gap']
    node_limit = options['mip_max_nodes']
    time_limit = options['time_limit']
    disp = options['log_to_console'] and options['output_flag']
    start = time.perf_counter()

    is_int = (integrality == 1) | (integrality == 3)
    is_semi = integrality >= 2
    lb = lb.copy()
    ub = ub.copy()
    lb[is_int] = np.ceil(lb[is_int] - tol)
    ub[is_int] = np.floor(ub[is_int] + tol)
    # Semi variable without values within its bounds can only be 0
    only_zero = is_semi & (lb > ub)
    lb[only_zero] = 0
    ub[only_zero] = 0
    # Semi variable with 0 within its bounds is a plain variable
    is_semi &= ~(lb <= 0)
    if np.any(lb > ub):
        return {'status': HighsModelStatus.kInfeasible}
    semi_lb = lb.copy()
    semi_ub = ub.copy()
    lb[is_semi] = 0

    # Heap entries are (bound, tie_breaker, lb, ub, semi_open),
    # bound is the objective of the parent LP relaxation.
    heap = []
    counter = itertools.count()
    node = (-np.inf, next(counter), lb, ub, is_semi)
    best_x = None
    best_fun = np.inf
    cutoff = np.inf
    pruned_bound = np.inf
    node_count = 0
    stop_status = None

    while node is not None or heap:
        if node is None:
            node = heapq.heappop(heap)
        bound, _, lb, ub, semi_open = node
        node = None
        if bound >= cutoff:
            pruned_bound = min(pruned_bound, bound)
            continue
        if node_limit is not None and node_count >= node_limit:
            stop_status = HighsModelStatus.kSolutionLimit
        elif time.perf_counter() - start >= time_limit:
            stop_status = HighsModelStatus.kTimeLimit
        if stop_status is not None:
            heapq.heappush(heap, (bound, next(counter), lb, ub, semi_open))
            break

        status, x, fun, _ = lp.solve(lb, ub)
        node_count += 1
        if status == 'infeasible':
            continue
        if status == 'unbounded':
            return {'status': HighsModelStatus.kUnboundedOrInfeasible}
        if status == 'failed':
            return {'status': HighsModelStatus.kSolveError}
        if status == 'iteration_limit':
            heapq.heappush(heap, (bound, next(counter), lb, ub, semi_open))
            stop_status = HighsModelStatus.kIterationLimit
            break
        if fun >= cutoff:
            pruned_bound = min(pruned_bound, fun)
            continue

        # Pick the violated variable with the largest score
        frac = np.abs(x - np.round(x))
        score = np.where(is_int & (frac > tol), frac, 0.)
        zero = np.abs(x) <= tol
        within = (x >= semi_lb - tol) & (x <= semi_ub + tol) & (~is_int | (frac <= tol))
        semi_violated = semi_open & ~zero & ~within
        # Resolve semi variables first
        score[semi_violated] = 1.
        j = int(np.argmax(score))

        if score[j] <= 0:
            x = x.copy()
            x[is_int] = np.round(x[is_int])
            x[semi_open & zero] = 0.
            x += 0.  # Avoid -0.
            fun = float(c @ x)
            if fun < best_fun:
                best_x, best_fun = x, fun
                cutoff = best_fun - max(abs_gap, rel_gap * abs(best_fun))
                if disp:
                    print(f'milp: node {node_count}, new incumbent {best_fun:.10g}')
            continue

        if semi_violated[j]:
            # Child with x_j == 0 and child with x_j in [semi_lb, semi_ub]
            child_open = semi_open.copy()
            child_open[j] = False
            zero_lb, zero_ub = lb.copy(), ub.copy()
            zero_lb[j] = zero_ub[j] = 0.
            on_lb, on_ub = lb.copy(), ub.copy()
            on_lb[j], on_ub[j] = semi_lb[j], semi_ub[j]
            children = [(zero_lb, zero_ub, child_open), (on_lb, on_ub, child_open)]
            if x[j] > semi_lb[j] - x[j]:
                children.reverse()
        else:
            down_ub = ub.copy()
            down_ub[j] = np.floor(x[j])
            up_lb = lb.copy()
            up_lb[j] = np.ceil(x[j])
            children = [(lb, down_ub, semi_open), (up_lb, ub, semi_open)]
            if x[j] - np.floor(x[j]) >= 0.5:
                children.reverse()
        # LP solution may be slightly out of bounds, which empties a child
        children = [child for child in children if child[0][j] <= child[1][j]]
        # Dive into the first child, queue the other one
        for child in children[1:]:
            heapq.heappush(heap, (fun, next(counter)) + child)
        if children:
            node = (fun, next(counter)) + children[0]

    if disp:
        print(f'milp: {node_count} LP relaxations solved')

    if stop_status is None:
        if best_x is None:
            return {'status': HighsModelStatus.kInfeasible}
        stop_status = HighsModelStatus.kOptimal
    dual_bound = min([best_fun, pruned_bound] + [entry[0] for entry in heap])
    if not np.isfinite(best_fun):
        gap = np.inf
    elif best_fun == 0:
        gap = 0. if dual_bound == 0 else np.inf
    else:
        gap = abs(best_fun - dual_bound) / abs(best_fun)
    return {'status': stop_status, 'x': best_x, 'fun': best_fun,
            'mip_node_count': node_count, 'mip_dual_bound': dual_bound, 'mip_gap': gap}


def _solve_lp(lp, lb, ub, options):
    """
    Returns:
        dict: status, x, fun.
    """
    if options['time_limit'] <= 0:
        return {'status': HighsModelStatus.kTimeLimit}
    status, x, fun, _ = lp.solve(lb, ub)
    if status == 'optimal':
        return {'status': HighsModelStatus.kOptimal, 'x': x, 'fun': fun}
    return {'status': {
        'infeasible': HighsModelStatus.kInfeasible,
        'unbounded': HighsModelStatus.kUnbounded,
        'iteration_limit': HighsModelStatus.kIterationLimit,
        'failed': HighsModelStatus.kSolveError,
    }[status]}


def _highs_wrapper(c, indptr, indices, data, lhs, rhs, lb, ub, integrality, options):
    """
    Backport of scipy.optimize._highspy._highs_wrapper._highs_wrapper.

        min c @ x
        such that  lhs <= A @ x <= rhs
                   lb <= x <= ub
                   integrality as in milp

    Args:
        c (np.ndarray): 1D objective coefficients.
        indptr, indices, data (np.ndarray): A in CSC format.
        lhs, rhs (np.ndarray): 1D constraint bounds.
        lb, ub (np.ndarray): 1D variable bounds.
        integrality (np.ndarray): uint8 integrality of each variable, or empty if all continuous.
        options (dict): HiGHS options.

    Returns:
        dict: Same as SciPy's without dual values. status is a HighsModelStatus.
            If a solution is found, x, slack, fun, simplex_nit, ipm_nit, crossover_nit,
            and mip_node_count, mip_dual_bound, mip_gap for MIP.
    """
    numcol = c.size
    numrow = rhs.size
    isMip = integrality is not None and np.sum(integrality) > 0
    integrality = np.asarray(integrality, dtype=np.uint8) if isMip else np.zeros(numcol, dtype=np.uint8)

    # default "null" return values
    res = {
        'x': None,
        'fun': None,
    }
    options = _highs_options(options)

    def run_error(status):
        res.update({'status': status, 'message': MODEL_STATUS_STRING[status]})
        return res

    # Invalid models, as HiGHS rejects them
    if np.any(lb == np.inf) or np.any(ub == -np.inf) or np.any(lhs == np.inf) or np.any(rhs == -np.inf):
        return run_error(HighsModelStatus.kModelError)
    if np.any((integrality >= 2) & (lb < 0)):
        return run_error(HighsModelStatus.kSolveError)

    A = sps.csc_matrix((data, indices, indptr), shape=(numrow, numcol)).toarray()
    lp = _LPRelaxation(c, A, lhs, rhs, presolve=options['presolve'],
                       simplex_iteration_limit=options['simplex_iteration_limit'],
                       ipm_iteration_limit=options['ipm_iteration_limit'])
    if np.any(lhs > rhs) or np.any((lb > ub) & (integrality < 2)):
        result = {'status': HighsModelStatus.kInfeasible}
    elif isMip:
        result = _branch_and_bound(lp, c, integrality, lb, ub, options)
    else:
        result = _solve_lp(lp, lb, ub, options)
    model_status = result['status']
    if model_status == HighsModelStatus.kSolveError:
        return run_error(model_status)

    if isMip:
        nit = {'simplex_nit': lp.nit['simplex'] + lp.nit['ipm'], 'ipm_nit': -1, 'crossover_nit': -1}
    else:
        nit = {'simplex_nit': lp.nit['simplex'], 'ipm_nit': lp.nit['ipm'], 'crossover_nit': 0}

    # Failure modes, as SciPy's _highs_wrapper
    x = result.get('x', None)
    mipFailCondition = model_status not in (
        HighsModelStatus.kOptimal,
        HighsModelStatus.kTimeLimit,
        HighsModelStatus.kIterationLimit,
        HighsModelStatus.kSolutionLimit,
    ) or x is None
    lpFailCondition = model_status != HighsModelStatus.kOptimal
    if (isMip and mipFailCondition) or (not isMip and lpFailCondition):
        primal_status = 'Feasible' if model_status == HighsModelStatus.kUnbounded else 'None'
        res.update({
            'status': model_status,
            'message': f'model_status is {MODEL_STATUS_STRING[model_status]}; '
                       f'primal_status is {primal_status}',
        })
        res.update(nit)
        return res

    res.update({
        'status': model_status,
        'message': MODEL_STATUS_STRING[model_status],
        'x': np.array(x),
        # Ax + s = b => Ax = b - s
        'slack': rhs - A @ x,
        'fun': result['fun'],
    })
    res.update(nit)
    if isMip:
        res.update({
            'mip_node_count': result['mip_node_count'],
            'mip_dual_bound': result['mip_dual_bound'],
            'mip_gap': result['mip_gap'],
        })
    return res
