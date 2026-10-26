"""Backport of scipy.optimize.milp for the pinned SciPy 1.4.1.

SciPy added `milp` in 1.9.0 as a wrapper of HiGHS, which SciPy 1.4.1 does not
ship. This module ports `milp` and the `LinearConstraint` and `Bounds`
arguments it takes, on top of the HiGHS interface backported in
module.island_handler.highs. After upgrading SciPy, only the import needs to change:

    from module.island_handler.milp import Bounds, LinearConstraint, milp
    from scipy.optimize import Bounds, LinearConstraint, milp

Differences from SciPy with HiGHS are listed in module.island_handler.highs.
"""
import warnings

import numpy as np
from scipy.optimize import Bounds as _Bounds
from scipy.optimize import LinearConstraint as _LinearConstraint
from scipy.optimize import OptimizeResult
from scipy.sparse import csc_matrix, issparse, vstack

from module.island_handler.highs import _highs_to_scipy_status_message, _highs_wrapper

__all__ = ['Bounds', 'LinearConstraint', 'milp']


class LinearConstraint(_LinearConstraint):
    """
    scipy.optimize.LinearConstraint with the default limits and input
    validation of later SciPy versions, `lb <= A @ x <= ub`.
    """

    def __init__(self, A, lb=-np.inf, ub=np.inf, keep_feasible=False):
        if not issparse(A):
            with warnings.catch_warnings():
                warnings.simplefilter('error')
                self.A = np.atleast_2d(A).astype(np.float64)
        else:
            self.A = A
        if issparse(lb) or issparse(ub):
            raise ValueError('Constraint limits must be dense arrays.')
        self.lb = np.atleast_1d(lb).astype(np.float64)
        self.ub = np.atleast_1d(ub).astype(np.float64)
        if issparse(keep_feasible):
            raise ValueError('`keep_feasible` must be a dense array.')
        self.keep_feasible = np.atleast_1d(keep_feasible).astype(bool)
        self._input_validation()

    def _input_validation(self):
        if self.A.ndim != 2:
            raise ValueError('`A` must have exactly two dimensions.')
        try:
            shape = self.A.shape[0:1]
            self.lb = np.broadcast_to(self.lb, shape)
            self.ub = np.broadcast_to(self.ub, shape)
            self.keep_feasible = np.broadcast_to(self.keep_feasible, shape)
        except ValueError:
            raise ValueError('`lb`, `ub`, and `keep_feasible` must be broadcastable '
                             'to shape `A.shape[0:1]`')

    def residual(self, x):
        return self.A @ x - self.lb, self.ub - self.A @ x


class Bounds(_Bounds):
    """
    scipy.optimize.Bounds with the default limits and input validation of
    later SciPy versions, `lb <= x <= ub`.
    """

    def __init__(self, lb=-np.inf, ub=np.inf, keep_feasible=False):
        if issparse(lb) or issparse(ub):
            raise ValueError('Lower and upper bounds must be dense arrays.')
        self.lb = np.atleast_1d(lb)
        self.ub = np.atleast_1d(ub)
        if issparse(keep_feasible):
            raise ValueError('`keep_feasible` must be a dense array.')
        self.keep_feasible = np.atleast_1d(keep_feasible).astype(bool)
        self._input_validation()

    def _input_validation(self):
        if self.lb.size == 0 or self.ub.size == 0:
            raise ValueError('`lb` and `ub` must be non-empty.')
        try:
            self.lb, self.ub, self.keep_feasible = np.broadcast_arrays(
                self.lb, self.ub, self.keep_feasible)
        except ValueError:
            raise ValueError('`lb`, `ub`, and `keep_feasible` must be broadcastable.')

    def __repr__(self):
        start = f'{type(self).__name__}({self.lb!r}, {self.ub!r}'
        if np.any(self.keep_feasible):
            end = f', keep_feasible={self.keep_feasible!r})'
        else:
            end = ')'
        return start + end

    def residual(self, x):
        return x - self.lb, self.ub - x


def _constraints_to_components(constraints):
    """
    Convert sequence of constraints to a single set of components A, b_l, b_u.

    `constraints` could be

    1. A LinearConstraint
    2. A tuple representing a LinearConstraint
    3. An invalid object
    4. A sequence of composed entirely of objects of type 1/2
    5. A sequence containing at least one object of type 3

    We want to accept 1, 2, and 4 and reject 3 and 5.
    """
    message = ('`constraints` (or each element within `constraints`) must be '
               'convertible into an instance of '
               '`scipy.optimize.LinearConstraint`.')
    As = []
    b_ls = []
    b_us = []

    # Accept case 1 by standardizing as case 4
    if isinstance(constraints, _LinearConstraint):
        constraints = [constraints]
    else:
        # Reject case 3
        try:
            iter(constraints)
        except TypeError as exc:
            raise ValueError(message) from exc

        # Accept case 2 by standardizing as case 4
        if len(constraints) == 3:
            # argument could be a single tuple representing a LinearConstraint
            try:
                constraints = [LinearConstraint(*constraints)]
            except (TypeError, ValueError, np.VisibleDeprecationWarning):
                # argument was not a tuple representing a LinearConstraint
                pass

    # Address cases 4/5
    for constraint in constraints:
        # if it's not a LinearConstraint or something that represents a
        # LinearConstraint at this point, it's invalid
        if not isinstance(constraint, LinearConstraint):
            try:
                if isinstance(constraint, _LinearConstraint):
                    # SciPy 1.4.1 LinearConstraint does not broadcast lb and ub
                    constraint = LinearConstraint(constraint.A, constraint.lb, constraint.ub)
                else:
                    constraint = LinearConstraint(*constraint)
            except TypeError as exc:
                raise ValueError(message) from exc
        As.append(csc_matrix(constraint.A))
        b_ls.append(np.atleast_1d(constraint.lb).astype(np.float64))
        b_us.append(np.atleast_1d(constraint.ub).astype(np.float64))

    if len(As) > 1:
        A = vstack(As, format='csc')
        b_l = np.concatenate(b_ls)
        b_u = np.concatenate(b_us)
    else:  # avoid unnecessary copying
        A = As[0]
        b_l = b_ls[0]
        b_u = b_us[0]

    return A, b_l, b_u


def _milp_iv(c, integrality, bounds, constraints, options):
    # objective IV
    if issparse(c):
        raise ValueError('`c` must be a dense array.')
    c = np.atleast_1d(c).astype(np.float64)
    if c.ndim != 1 or c.size == 0 or not np.all(np.isfinite(c)):
        message = ('`c` must be a one-dimensional array of finite numbers '
                   'with at least one element.')
        raise ValueError(message)

    # integrality IV
    if issparse(integrality):
        raise ValueError('`integrality` must be a dense array.')
    message = ('`integrality` must contain integers 0-3 and be broadcastable '
               'to `c.shape`.')
    if integrality is None:
        integrality = 0
    try:
        integrality = np.broadcast_to(integrality, c.shape).astype(np.uint8)
    except ValueError:
        raise ValueError(message)
    if integrality.min() < 0 or integrality.max() > 3:
        raise ValueError(message)

    # bounds IV
    if bounds is None:
        bounds = Bounds(0, np.inf)
    elif not isinstance(bounds, _Bounds):
        message = ('`bounds` must be convertible into an instance of '
                   '`scipy.optimize.Bounds`.')
        try:
            bounds = Bounds(*bounds)
        except TypeError as exc:
            raise ValueError(message) from exc

    try:
        lb = np.broadcast_to(bounds.lb, c.shape).astype(np.float64)
        ub = np.broadcast_to(bounds.ub, c.shape).astype(np.float64)
    except (ValueError, TypeError) as exc:
        message = ('`bounds.lb` and `bounds.ub` must contain reals and '
                   'be broadcastable to `c.shape`.')
        raise ValueError(message) from exc

    # constraints IV
    if not constraints:
        constraints = [LinearConstraint(np.empty((0, c.size)),
                                        np.empty((0,)), np.empty((0,)))]
    try:
        A, b_l, b_u = _constraints_to_components(constraints)
    except ValueError as exc:
        message = ('`constraints` (or each element within `constraints`) must '
                   'be convertible into an instance of '
                   '`scipy.optimize.LinearConstraint`.')
        raise ValueError(message) from exc

    if A.shape != (b_l.size, c.size):
        message = 'The shape of `A` must be (len(b_l), len(c)).'
        raise ValueError(message)
    indptr, indices, data = A.indptr, A.indices, A.data.astype(np.float64)

    # options IV, as SciPy does, this pops keys from the caller's dict
    options = options or {}
    supported_options = {'disp', 'presolve', 'time_limit', 'node_limit',
                         'mip_rel_gap'}
    unsupported_options = set(options).difference(supported_options)
    if unsupported_options:
        message = (f'Unrecognized options detected: {unsupported_options}. '
                   'These will be passed to HiGHS verbatim.')
        warnings.warn(message, RuntimeWarning, stacklevel=3)
    options_iv = {'log_to_console': options.pop('disp', False),
                  'mip_max_nodes': options.pop('node_limit', None)}
    options_iv.update(options)

    return c, integrality, lb, ub, indptr, indices, data, b_l, b_u, options_iv


def milp(c, *, integrality=None, bounds=None, constraints=None, options=None):
    r"""
    Mixed-integer linear programming, same interface as scipy.optimize.milp.

        min_x  c @ x
        such that  b_l <= A @ x <= b_u
                   l <= x <= u
                   Specified elements of x must be integers

    By default, ``l = 0`` and ``u = np.inf`` unless specified with ``bounds``.

    Args:
        c (array_like): 1D coefficients of the linear objective function to be minimized.
        integrality (array_like): 1D type of integrality constraint on each decision variable.
            0: Continuous variable.
            1: Integer variable within `bounds`.
            2: Semi-continuous variable, within `bounds` or 0.
            3: Semi-integer variable, an integer within `bounds` or 0.
            All variables are continuous by default.
        bounds (Bounds): Bounds on the decision variables. Non-negative by default.
        constraints (LinearConstraint, tuple, or sequence of them):
            Linear constraints. ``keep_feasible`` is ignored.
        options (dict): Solver options.
            disp (bool): Print progress, default False.
            node_limit (int): Maximum number of nodes to solve, no maximum by default.
            presolve (bool): Presolve, default True.
            time_limit (float): Maximum seconds to solve, no limit by default.
            mip_rel_gap (float): Terminate when the gap between the primal objective value
                and the dual objective bound, scaled by the primal objective value,
                is <= mip_rel_gap. Default 1e-4.

    Returns:
        OptimizeResult: with attributes
            status (int): 0 optimal solution found, 1 iteration or time limit reached,
                2 problem is infeasible, 3 problem is unbounded, 4 other, see message.
            success (bool): True when an optimal solution is found.
            message (str): Descriptor of the exit status.
            x (np.ndarray | None): Values of the decision variables.
            fun (float | None): Optimal value of the objective function ``c @ x``.
            mip_node_count (int | None): Number of nodes solved.
            mip_dual_bound (float | None): Final lower bound on the optimal solution.
            mip_gap (float | None): The difference between the primal objective value
                and the dual objective bound, scaled by the primal objective value.
    """
    args_iv = _milp_iv(c, integrality, bounds, constraints, options)
    c, integrality, lb, ub, indptr, indices, data, b_l, b_u, options = args_iv

    highs_res = _highs_wrapper(c, indptr, indices, data, b_l, b_u,
                               lb, ub, integrality, options)

    res = {}

    # Convert to scipy-style status and message
    highs_status = highs_res.get('status', None)
    highs_message = highs_res.get('message', None)
    status, message = _highs_to_scipy_status_message(highs_status,
                                                     highs_message)
    res['status'] = status
    res['message'] = message
    res['success'] = (status == 0)
    x = highs_res.get('x', None)
    res['x'] = np.array(x) if x is not None else None
    res['fun'] = highs_res.get('fun', None)
    res['mip_node_count'] = highs_res.get('mip_node_count', None)
    res['mip_dual_bound'] = highs_res.get('mip_dual_bound', None)
    res['mip_gap'] = highs_res.get('mip_gap', None)

    return OptimizeResult(res)
