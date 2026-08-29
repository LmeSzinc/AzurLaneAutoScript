"""Phase 4A converter: split a legacy map .py into <name>.json + logic fragment.

Usage:
    .venv\\Scripts\\python.exe dev_tools/campaign_to_json.py <folder> [--name <name>]

Rules (spec phase456_flash_execution.md S7.2):
- Only files containing `MAP = CampaignMap(` are converted; campaign_base.py skipped.
- MAP.<attr> = <literal>            -> json["map"][attr]  (file order preserved)
- MAP.<method>(...) top-level calls -> json["actions"] (grid names become strings)
- road_x = RoadGrids([A1, ...])     -> json["roads"]["x"] = ["A1", ...]
- from .x import Config as ConfigBase -> json["config_base"] = "x"
  (cross-folder: from campaign.a.b import ... -> "a.b")
- class Config: every NAME = <literal> -> json["config"]; methods -> SKIP file
- class Campaign: everything except `MAP = MAP` -> fragment .py (ast.unparse)
- flatten statement -> dropped
- Any other top-level statement -> SKIP file (logged)
- A semantic snapshot of the pre-conversion state is written to
  .legacy_snapshot/<name>.snapshot.json for verify_map_data.py.
"""
import ast
import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN = ROOT / 'campaign'


def node_name(node):
    if isinstance(node, ast.Name):
        return node.id
    raise ValueError(f'not a name: {ast.dump(node)[:80]}')


def flatten_list(node):
    """Flatten List/BinOp(Add) into item nodes (road/select grid names)."""
    if isinstance(node, ast.List):
        return node.elts
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return flatten_list(node.left) + flatten_list(node.right)
    raise ValueError(f'not a flat list: {ast.dump(node)[:80]}')


def grid_name(node):
    """Resolve a grid reference node to its node string ('B4')."""
    if isinstance(node, ast.Name):
        return node.id
    raise ValueError(f'not a grid name: {ast.dump(node)[:80]}')


def safe_eval(node):
    """Evaluate constant expressions: arithmetic over literals allowed."""
    try:
        return ast.literal_eval(node)
    except Exception:
        try:
            expr = ast.Expression(body=node)
            return eval(compile(expr, '<campaign cfg>', 'eval'), {'__builtins__': {}})
        except Exception:
            raise ValueError(f'unsupported expression: {ast.dump(node)[:80]}') from None


def parse_road_expr(node):
    """Road expression DSL: RoadGrids(...) / .combine(...) / ref / list of refs."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id == 'RoadGrids':
        groups = []
        for item in flatten_list(node.args[0]):
            if isinstance(item, ast.List):
                groups.append([grid_name(e) for e in item.elts])
            else:
                groups.append([grid_name(item)])
        return {'roadgrids': groups}
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr == 'combine':
        return {'combine': [parse_road_expr(node.func.value), parse_road_expr(node.args[0])]}
    if isinstance(node, ast.Name):
        return {'ref': node.id}
    if isinstance(node, ast.List):
        return {'list': [parse_road_expr(e) for e in node.elts]}
    raise ValueError(f'unsupported road expr: {ast.dump(node)[:80]}')


def literal_or_name(node):
    """Return (kind, value) where kind is 'literal'|'grid'."""
    if isinstance(node, ast.Name) and node.id and node.id[0].isalpha() and node.id[1:].isdigit():
        return 'grid', node.id
    try:
        return 'literal', ast.literal_eval(node)
    except Exception:
        raise ValueError(f'unconvertible node: {ast.dump(node)[:80]}') from None


def convert(path: Path):
    src = path.read_text(encoding='utf-8')
    tree = ast.parse(src)

    map_objects: dict[str, dict] = {}  # var name -> {'attrs': {}, 'actions': []}
    import_map: dict[str, str] = {}  # imported name -> module path (campaign-relative)
    roads = {}
    selects = {}
    config_base = None
    config = {}
    campaign_nodes = []
    skip_reason = None

    def resolve_ref(name):
        """Resolve a bare Name value to a campaign-relative module path string."""
        if name in import_map:
            return import_map[name]
        raise ValueError(f'name not imported: {name}')

    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            continue  # module docstring
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom):
                rel = node.level
                module = node.module or ''
                if rel > 0:
                    # .campaign_15_base -> 'campaign_15_base' (folder-relative);
                    # multi-level: '<folder>.sub.module'
                    target = module if rel == 1 else f'{path.parent.name}.{module}'
                elif module.startswith('campaign.'):
                    target = '.'.join(module.split('.')[1:])
                else:
                    target = module
                for alias in node.names:
                    if alias.name == 'Config' and alias.asname == 'ConfigBase':
                        config_base = target
                    elif alias.asname:
                        import_map[alias.asname] = f'{target}.{alias.name}'
                    else:
                        import_map[alias.name] = f'{target}.{alias.name}'
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name) and isinstance(node.value, ast.Call) \
                    and isinstance(node.value.func, ast.Name) \
                    and node.value.func.id == 'CampaignMap':
                map_name = None
                for kw in node.value.keywords:
                    if kw.arg == 'name' or (kw.arg is None and len(node.value.args) == 1):
                        map_name = ast.literal_eval(kw.value)
                map_objects.setdefault(tgt.id, {'attrs': {}, 'actions': []})
                if map_name is not None:
                    map_objects[tgt.id]['attrs']['name'] = map_name
                continue
            if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) \
                    and tgt.value.id in map_objects:
                try:
                    value = safe_eval(node.value)
                except ValueError:
                    if isinstance(node.value, ast.Name):
                        value = {'__ref__': resolve_ref(node.value.id)}
                    else:
                        skip_reason = f'unsupported MAP attr {ast.unparse(node)[:60]}'
                        break
                map_objects[tgt.value.id]['attrs'][tgt.attr] = value
                continue
            if isinstance(tgt, ast.Name):
                try:
                    roads[tgt.id] = parse_road_expr(node.value)
                    continue
                except ValueError:
                    pass
                if isinstance(node.value, ast.Call) \
                        and isinstance(node.value.func, ast.Name) \
                        and node.value.func.id == 'SelectedGrids':
                    selects[tgt.id] = [grid_name(e) for e in flatten_list(node.value.args[0])]
                    continue
            if isinstance(tgt, ast.Tuple) and isinstance(node.value, ast.Call) \
                    and isinstance(node.value.func, ast.Attribute) \
                    and node.value.func.attr == 'flatten':
                continue  # A1, B1, ... = MAP.flatten()
            skip_reason = f'top-level assign {ast.unparse(node)[:60]}'
            break
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) \
                and isinstance(node.value.func, ast.Attribute) \
                and isinstance(node.value.func.value, ast.Name) \
                and node.value.func.value.id in map_objects:
            call = node.value
            args = [literal_or_name(a)[1] for a in call.args]
            kwargs = {kw.arg: literal_or_name(kw.value)[1] for kw in call.keywords}
            map_objects[call.func.value.id]['actions'].append(
                {'call': call.func.attr, 'args': args, 'kwargs': kwargs}
            )
            continue
        if isinstance(node, ast.ClassDef) and node.name == 'Config':
            for sub in node.body:
                if isinstance(sub, ast.Assign) and len(sub.targets) == 1 \
                        and isinstance(sub.targets[0], ast.Name):
                    config[sub.targets[0].id] = safe_eval(sub.value)
                elif isinstance(sub, (ast.Expr, ast.Pass)):
                    continue
                else:
                    skip_reason = f'Config has non-literal member {ast.unparse(sub)[:60]}'
            if skip_reason:
                break
            continue
        if isinstance(node, ast.ClassDef) and node.name == 'Campaign':
            for sub in node.body:
                if isinstance(sub, ast.Assign) and len(sub.targets) == 1 \
                        and isinstance(sub.targets[0], ast.Name) and sub.targets[0].id == 'MAP':
                    continue  # MAP = MAP
                campaign_nodes.append(sub)
            continue
        skip_reason = f'top-level {type(node).__name__} {ast.unparse(node)[:60]}'
        break

    if skip_reason:
        return None, skip_reason

    if 'MAP' not in map_objects:
        return None, 'no MAP data'

    primary = map_objects['MAP']
    data = {
        'map': primary['attrs'],
        'config_base': config_base,
        'config': config,
        'roads': roads,
        'selects': selects,
        'actions': primary['actions'],
        'extra_maps': {k: v for k, v in map_objects.items() if k != 'MAP'},
    }
    fragment = 'class Campaign(CampaignBase):\n' + '\n'.join(
        textwrap.indent(ast.unparse(n), '    ') for n in campaign_nodes
    ) + '\n'

    snapshot = {
        'map': data['map'],
        'config_base': config_base,
        'config': config,
        'roads': roads,
        'selects': selects,
        'actions': data['actions'],
        'extra_maps': data['extra_maps'],
        'campaign_methods': sorted(
            n.name for n in campaign_nodes if isinstance(n, ast.FunctionDef)
        ),
    }
    return (data, fragment, snapshot), None


def main():
    if len(sys.argv) < 2:
        sys.exit('usage: campaign_to_json.py <folder> [--name <name>]')
    folder = sys.argv[1]
    only = None
    if len(sys.argv) == 4 and sys.argv[2] == '--name':
        only = sys.argv[3]

    folder_path = CAMPAIGN / folder
    if not folder_path.exists():
        sys.exit(f'folder not found: {folder_path}')

    snap_dir = folder_path / '.legacy_snapshot'
    snap_dir.mkdir(exist_ok=True)
    converted, skipped, nonmaps = [], [], []
    for py in sorted(folder_path.glob('*.py')):
        if py.name == 'campaign_base.py' or not py.name.endswith('.py'):
            continue
        if only and py.stem != only:
            continue
        if 'MAP = CampaignMap(' not in py.read_text(encoding='utf-8'):
            nonmaps.append(py.name)  # base/Config-only files stay untouched
            continue
        try:
            result, reason = convert(py)
        except Exception as e:
            result, reason = None, f'exception {e}'
        if result is None:
            skipped.append(f'{py.name}: {reason}')
            continue
        data, fragment, snapshot = result
        (folder_path / f'{py.stem}.json').write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n'
        )
        py.write_text(fragment, encoding='utf-8', newline='\n')
        (snap_dir / f'{py.stem}.snapshot.json').write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n'
        )
        converted.append(py.stem)

    print(f'CONVERTED {folder}: {len(converted)} maps, {len(skipped)} skipped, '
          f'{len(nonmaps)} non-map files left as-is')
    for line in skipped:
        print('  SKIP', line)
    (snap_dir / 'skipped.txt').write_text('\n'.join(skipped) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
