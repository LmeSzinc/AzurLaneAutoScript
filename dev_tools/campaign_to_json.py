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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN = ROOT / 'campaign'


def node_name(node):
    if isinstance(node, ast.Name):
        return node.id
    raise ValueError(f'not a name: {ast.dump(node)[:80]}')


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
    name = path.stem

    map_attrs = {}
    actions = []
    roads = {}
    config_base = None
    config = {}
    campaign_nodes = []
    skip_reason = None
    map_name = None

    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            continue  # module docstring
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == 'Config' and alias.asname == 'ConfigBase':
                        rel = node.level
                        if rel > 0:
                            # from .x import ... -> 'x'; from .sub.x import ... -> '<folder>.sub.x'
                            tail = node.module or ''
                            config_base = tail if rel == 1 else f'{path.parent.name}.{tail}'
                        else:
                            # from campaign.a.b import ... -> 'a.b'
                            config_base = '.'.join((node.module or '').split('.')[1:])
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name) and tgt.id == 'MAP' and isinstance(node.value, ast.Call):
                for kw in node.value.keywords:
                    if kw.arg == 'name' or (kw.arg is None and len(node.value.args) == 1):
                        map_name = ast.literal_eval(kw.value)
                continue
            if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) \
                    and tgt.value.id == 'MAP':
                map_attrs[tgt.attr] = ast.literal_eval(node.value)
                continue
            if isinstance(tgt, ast.Name) and tgt.id.startswith('road_') \
                    and isinstance(node.value, ast.Call):
                grid_names = [node_name(e) for e in node.value.args[0].elts]
                roads[tgt.id[len('road_'):]] = grid_names
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
                and node.value.func.value.id == 'MAP':
            call = node.value
            args = [literal_or_name(a)[1] for a in call.args]
            kwargs = {kw.arg: literal_or_name(kw.value)[1] for kw in call.keywords}
            actions.append({'call': call.func.attr, 'args': args, 'kwargs': kwargs})
            continue
        if isinstance(node, ast.ClassDef) and node.name == 'Config':
            for sub in node.body:
                if isinstance(sub, ast.Assign) and len(sub.targets) == 1 \
                        and isinstance(sub.targets[0], ast.Name):
                    config[sub.targets[0].id] = ast.literal_eval(sub.value)
                elif isinstance(sub, ast.Expr) and isinstance(sub.value, ast.Constant):
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

    if not map_attrs and map_name is None:
        return None, 'no MAP data'

    data = {
        'map': ({'name': map_name} if map_name else {}) | map_attrs,
        'config_base': config_base,
        'config': config,
        'roads': roads,
        'actions': actions,
    }
    fragment = 'class Campaign(CampaignBase):\n' + '\n'.join(ast.unparse(n) for n in campaign_nodes) + '\n'

    snapshot = {
        'map': data['map'],
        'config_base': config_base,
        'config': config,
        'roads': roads,
        'actions': actions,
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
    converted, skipped = [], []
    for py in sorted(folder_path.glob('*.py')):
        if py.name == 'campaign_base.py' or not py.name.endswith('.py'):
            continue
        if only and py.stem != only:
            continue
        try:
            result, reason = convert(py)
        except Exception as e:  # noqa: BLE001 - converter must report per file
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

    print(f'CONVERTED {folder}: {len(converted)} maps, {len(skipped)} skipped')
    for line in skipped:
        print('  SKIP', line)
    (snap_dir / 'skipped.txt').write_text('\n'.join(skipped) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
