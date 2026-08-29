"""Phase 456 battle-pattern library: declarative battle method synthesis.

Fragment battle methods that match a known pattern are stored as a compact
spec in the map YAML (`battles: {battle_0: {pattern: clear_filter, ...}}`)
and synthesized onto the Campaign class by map_loader. Equivalence is
structural: `canonical_source(name, spec)` must equal `ast.unparse()` of the
original method body - the transformer asserts this before extracting, and
verify_map_data re-asserts it against the recorded snapshot bodies.
"""
from __future__ import annotations

import ast
import typing as t


def _if_true(call: ast.expr) -> ast.If:
    return ast.If(test=call, body=[ast.Return(value=ast.Constant(value=True))], orelse=[])


def _call(attr: str, *args: ast.expr, **kwargs: ast.expr) -> ast.Call:
    return ast.Call(
        func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=attr, ctx=ast.Load()),
        args=list(args),
        keywords=[ast.keyword(arg=k, value=v) for k, v in kwargs.items()],
    )


def _ret_default() -> ast.Return:
    return ast.Return(value=_call('battle_default'))


def _const(value) -> ast.expr:
    return ast.Constant(value=value)


def _self_attr(attr: str) -> ast.expr:
    return ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=attr, ctx=ast.Load())


def _build_def(name: str, body: list[ast.stmt]) -> ast.FunctionDef:
    return ast.FunctionDef(
        name=name,
        args=ast.arguments(
            posonlyargs=[], args=[ast.arg(arg='self')], kwonlyargs=[], kw_defaults=[],
            vararg=None, kwarg=None, defaults=[],
        ),
        body=body,
        decorator_list=[],
        returns=None,
        type_comment=None,
    )


# --------------------------------------------------------------------------
# Builders (spec -> FunctionDef)
# --------------------------------------------------------------------------

def build_def(name: str, spec: dict) -> ast.FunctionDef:
    pattern = spec['pattern']
    if pattern == 'clear_filter':
        body = []
        if spec.get('siren'):
            body.append(_if_true(_call('clear_siren')))
        if spec.get('preserve') is not None:
            body.append(_if_true(_call('clear_filter_enemy', _self_attr('ENEMY_FILTER'),
                                       preserve=_const(spec['preserve']))))
        body.append(_ret_default())
    elif pattern == 'clear_siren':
        body = [_if_true(_call('clear_siren')), _ret_default()]
    elif pattern == 'default':
        body = [_ret_default()]
    elif pattern == 'boss':
        kind = spec['kind']
        if kind == 'clear':
            call = _call('clear_boss')
        elif kind == 'brute':
            call = _call('brute_clear_boss')
        else:
            call = ast.Call(
                func=ast.Attribute(value=ast.Attribute(
                    value=ast.Name(id='self', ctx=ast.Load()), attr=kind, ctx=ast.Load()),
                    attr='clear_boss', ctx=ast.Load()),
                args=[], keywords=[],
            )
        body = [ast.Return(value=call)]
    elif pattern == 'protect_siren':
        body = [_if_true(_call('fleet_2_protect')), _if_true(_call('clear_siren')), _ret_default()]
    elif pattern == 'mystery':
        body = [ast.Expr(value=_call('clear_all_mystery')), _ret_default()]
    elif pattern == 'clear_scale':
        body = []
        if spec.get('siren'):
            body.append(_if_true(_call('clear_siren')))
        for step in spec['scales']:
            kwargs: dict[str, ast.expr] = {}
            if step.get('genre') is not None:
                kwargs['genre'] = _const(step['genre'])
            body.append(_if_true(_call('clear_enemy', _const(step['scale']), **kwargs)))
        body.append(_ret_default())
    elif pattern == 'bouncing_filter':
        body = [_if_true(_call('clear_bouncing_enemy')), _if_true(_call('clear_siren'))]
        if spec.get('preserve') is not None:
            body.append(_if_true(_call('clear_filter_enemy', _self_attr('ENEMY_FILTER'),
                                       preserve=_const(spec['preserve']))))
        body.append(_ret_default())
    elif pattern == 'clear_mode_filter':
        inner = []
        if spec.get('siren'):
            inner.append(_if_true(_call('clear_siren')))
        if spec.get('preserve') is not None:
            inner.append(_if_true(_call('clear_filter_enemy', _self_attr('ENEMY_FILTER'),
                                        preserve=_const(spec['preserve']))))
        orelse: list[ast.stmt] = []
        if spec.get('else_sort') is not None:
            orelse.append(_if_true(_call('clear_any_enemy', sort=_const(spec['else_sort']))))
        body = [ast.If(test=_call('map_is_clear_mode'), body=inner, orelse=orelse)]
        body.append(_ret_default())
    elif pattern == 'roadblocks':
        args: list[ast.expr] = [ast.Name(id=spec['road'], ctx=ast.Load())]
        if spec.get('potential'):
            args.append(ast.keyword(arg='potential', value=_const(True)))
        body = [ast.Return(value=_call('battle_clear_roadblocks', *args))]
    else:
        raise ValueError(f'unknown pattern: {pattern}')
    return _build_def(name, body)


def canonical_source(name: str, spec: dict) -> str:
    return ast.unparse(ast.fix_missing_locations(build_def(name, spec)))


# --------------------------------------------------------------------------
# Matchers (FunctionDef -> spec or None). A matcher must only accept a body
# whose canonical form round-trips: the transformer asserts equality.
# --------------------------------------------------------------------------

def _match_clear_filter(body: list[ast.stmt]) -> dict | None:
    siren = False
    preserve: int | None = None
    i = 0
    if i < len(body) and isinstance(body[i], ast.If) and _is_call_true(body[i], 'clear_siren'):
        siren = True
        i += 1
    if i < len(body) and isinstance(body[i], ast.If):
        preserve = _preserve_of(body[i])
        if preserve is not None:
            i += 1
    if i == len(body) - 1 and _is_ret_call(body[i], 'battle_default'):
        return {'pattern': 'clear_filter', 'siren': siren, 'preserve': preserve}
    return None


def _is_call_true(node: ast.If, attr: str) -> bool:
    return (len(node.body) == 1 and isinstance(node.body[0], ast.Return)
            and isinstance(node.body[0].value, ast.Constant)
            and node.body[0].value.value is True
            and isinstance(node.test, ast.Call)
            and isinstance(node.test.func, ast.Attribute)
            and isinstance(node.test.func.value, ast.Name)
            and node.test.func.value.id == 'self'
            and node.test.func.attr == attr
            and not node.test.args)


def _is_true_if(node: ast.If, attr: str) -> bool:
    """Same as _is_call_true but allowing call arguments (clear_enemy etc.)."""
    return (len(node.body) == 1 and isinstance(node.body[0], ast.Return)
            and isinstance(node.body[0].value, ast.Constant)
            and node.body[0].value.value is True
            and isinstance(node.test, ast.Call)
            and isinstance(node.test.func, ast.Attribute)
            and isinstance(node.test.func.value, ast.Name)
            and node.test.func.value.id == 'self'
            and node.test.func.attr == attr)


def _preserve_of(node: ast.If) -> int | None:
    if not _is_true_if(node, 'clear_filter_enemy'):
        return None
    test = node.test
    arg0 = test.args[0] if test.args else None
    if not (isinstance(arg0, ast.Attribute) and isinstance(arg0.value, ast.Name)
            and arg0.value.id == 'self' and arg0.attr == 'ENEMY_FILTER'):
        return None
    for kw in test.keywords:
        if kw.arg == 'preserve' and isinstance(kw.value, ast.Constant):
            return kw.value.value
    return None


def _is_ret_call(node: ast.stmt, attr: str) -> bool:
    return (isinstance(node, ast.Return) and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == attr
            and not node.value.args and not node.value.keywords)


def _match_clear_mode_filter(body: list[ast.stmt]) -> dict | None:
    if not body or not isinstance(body[0], ast.If):
        return None
    test = body[0].test
    if not (isinstance(test, ast.Call) and isinstance(test.func, ast.Attribute)
            and test.func.attr == 'map_is_clear_mode'):
        return None
    inner = body[0].body
    spec: dict = {'pattern': 'clear_mode_filter', 'siren': False, 'preserve': None, 'else_sort': None}
    i = 0
    if i < len(inner) and isinstance(inner[i], ast.If) and _is_call_true(inner[i], 'clear_siren'):
        spec['siren'] = True
        i += 1
    if i < len(inner) and isinstance(inner[i], ast.If):
        p = _preserve_of(inner[i])
        if p is not None:
            spec['preserve'] = p
            i += 1
    if i != len(inner):
        return None
    # optional elif: clear_any_enemy(sort=...)
    orelse = body[0].orelse
    if orelse:
        if len(orelse) == 1 and isinstance(orelse[0], ast.If) \
                and _is_call_true(orelse[0], 'clear_any_enemy') and not orelse[0].orelse:
            for kw in orelse[0].test.keywords:
                if kw.arg == 'sort' and isinstance(kw.value, ast.Constant):
                    spec['else_sort'] = kw.value.value
        else:
            return None
    rest = body[1:]
    if len(rest) == 1 and _is_ret_call(rest[0], 'battle_default'):
        return spec
    return None


def _match_boss(body: list[ast.stmt]) -> dict | None:
    if len(body) != 1 or not isinstance(body[0], ast.Return) \
            or not isinstance(body[0].value, ast.Call):
        return None
    call = body[0].value
    if not isinstance(call.func, ast.Attribute) or call.args or call.keywords:
        return None
    if call.func.attr == 'brute_clear_boss' and isinstance(call.func.value, ast.Name) \
            and call.func.value.id == 'self':
        return {'pattern': 'boss', 'kind': 'brute'}
    if call.func.attr == 'clear_boss':
        base = call.func.value
        if isinstance(base, ast.Name) and base.id == 'self':
            return {'pattern': 'boss', 'kind': 'clear'}
        if isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name) \
                and base.value.id == 'self':
            return {'pattern': 'boss', 'kind': base.attr}
    return None

def _match_bouncing_filter(body: list[ast.stmt]) -> dict | None:
    spec: dict = {'pattern': 'bouncing_filter', 'preserve': None}
    i = 0
    if i < len(body) and isinstance(body[i], ast.If) and _is_call_true(body[i], 'clear_bouncing_enemy'):
        i += 1
    else:
        return None
    if i < len(body) and isinstance(body[i], ast.If) and _is_call_true(body[i], 'clear_siren'):
        i += 1
    else:
        return None
    if i < len(body) and isinstance(body[i], ast.If):
        p = _preserve_of(body[i])
        if p is not None:
            spec['preserve'] = p
            i += 1
    if i == len(body) - 1 and _is_ret_call(body[i], 'battle_default'):
        return spec
    return None


def _match_clear_scale(body: list[ast.stmt]) -> dict | None:
    spec: dict = {'pattern': 'clear_scale', 'siren': False, 'scales': []}
    i = 0
    if i < len(body) and isinstance(body[i], ast.If) and _is_call_true(body[i], 'clear_siren'):
        spec['siren'] = True
        i += 1
    while i < len(body) and isinstance(body[i], ast.If) and _is_true_if(body[i], 'clear_enemy'):
        test = body[i].test
        if len(test.args) != 1 or not isinstance(test.args[0], ast.Constant):
            return None
        scale = test.args[0].value
        if not isinstance(scale, tuple) or len(scale) != 1:
            return None
        step: dict = {'scale': scale[0], 'genre': None}
        for kw in test.keywords:
            if kw.arg == 'genre' and isinstance(kw.value, ast.Constant):
                step['genre'] = kw.value.value
        spec['scales'].append(step)
        i += 1
    if i == len(body) - 1 and _is_ret_call(body[i], 'battle_default'):
        return spec
    return None


def _match_roadblocks(body: list[ast.stmt]) -> dict | None:
    if len(body) != 1 or not isinstance(body[0], ast.Return) or not isinstance(body[0].value, ast.Call):
        return None
    call = body[0].value
    if not isinstance(call.func, ast.Attribute) or call.func.attr != 'battle_clear_roadblocks':
        return None
    if len(call.args) != 1 or not isinstance(call.args[0], ast.Name):
        return None
    spec: dict = {'pattern': 'roadblocks', 'road': call.args[0].id, 'potential': False}
    for kw in call.keywords:
        if kw.arg == 'potential' and isinstance(kw.value, ast.Constant):
            spec['potential'] = kw.value.value
    return spec


MATCHERS: list[t.Callable[[list[ast.stmt]], dict | None]] = [
    _match_clear_filter,
    _match_boss,
    lambda b: {'pattern': 'clear_siren'} if (
        len(b) == 2 and isinstance(b[0], ast.If) and _is_call_true(b[0], 'clear_siren')
        and _is_ret_call(b[1], 'battle_default')) else None,
    lambda b: {'pattern': 'default'} if (
        len(b) == 1 and _is_ret_call(b[0], 'battle_default')) else None,
    _match_clear_mode_filter,
    lambda b: {'pattern': 'protect_siren'} if (
        len(b) == 3 and isinstance(b[0], ast.If) and _is_call_true(b[0], 'fleet_2_protect')
        and isinstance(b[1], ast.If) and _is_call_true(b[1], 'clear_siren')
        and _is_ret_call(b[2], 'battle_default')) else None,
    lambda b: {'pattern': 'mystery'} if (
        len(b) == 2 and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Call)
        and isinstance(b[0].value.func, ast.Attribute) and b[0].value.func.attr == 'clear_all_mystery'
        and _is_ret_call(b[1], 'battle_default')) else None,
    _match_clear_scale,
    _match_bouncing_filter,
    _match_roadblocks,
    lambda b: None,
]


def match_body(body: list[ast.stmt]) -> dict | None:
    for matcher in MATCHERS:
        spec = matcher(body)
        if spec is not None:
            return spec
    return None


def synthesize(name: str, spec: dict, ns: dict) -> t.Callable:
    """Exec the canonical method source into `ns` and return the function."""
    src = canonical_source(name, spec)
    exec(compile(src, f'<battle {name}>', 'exec'), ns)
    return ns[name]
