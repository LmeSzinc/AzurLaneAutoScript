"""Phase 4B gate: semantic equivalence of assets.py before/after regeneration.

Usage:
    .venv\\Scripts\\python.exe dev_tools/verify_assets.py dump <out.json>
    .venv\\Scripts\\python.exe dev_tools/verify_assets.py check <snapshot.json>

`dump` walks module/**/assets.py, ast-parses every `NAME = Button(...)` /
`NAME = Template(...)` line and records the per-server (area, color, button,
file) quadruple. `check` re-dumps and requires deep equality against the
snapshot - so generator format changes (dict -> bare tuple broadcast) are
validated semantically, not textually.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVERS = ['cn', 'en', 'jp', 'tw']


def _literal(node):
    return ast.literal_eval(node)


def parse_assets():
    buttons = {}
    templates = {}
    unparsed = []
    for py in sorted((ROOT / 'module').rglob('assets.py')):
        rel = str(py.relative_to(ROOT)).replace('\\', '/')
        try:
            tree = ast.parse(py.read_text(encoding='utf-8'))
        except Exception as e:
            unparsed.append(f'{rel}: parse error {e}')
            continue
        for node in tree.body:
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            tgt = node.targets[0]
            if not isinstance(tgt, ast.Name) or not isinstance(node.value, ast.Call):
                continue
            call = node.value
            if not isinstance(call.func, ast.Name) or call.func.id not in ('Button', 'Template'):
                continue
            try:
                kwargs = {kw.arg: _literal(kw.value) for kw in call.keywords}
            except Exception:
                unparsed.append(f'{rel}:{node.lineno} {tgt.id} literal eval failed')
                continue
            if call.func.id == 'Template':
                entry = {'file': kwargs.get('file')}
                templates[tgt.id] = entry
            else:
                entry = {}
                for key in ('area', 'color', 'button', 'file'):
                    value = kwargs.get(key)
                    if isinstance(value, dict):
                        entry[key] = {s: value[s] for s in SERVERS}
                    else:
                        # bare value broadcasts across all four servers
                        entry[key] = {s: value for s in SERVERS}
                buttons[tgt.id] = entry
    return {'buttons': buttons, 'templates': templates, 'unparsed': unparsed}


def main():
    if len(sys.argv) != 3:
        sys.exit('usage: verify_assets.py dump <out.json> | check <snapshot.json>')
    mode, arg = sys.argv[1], sys.argv[2]
    if mode == 'dump':
        data = parse_assets()
        Path(arg).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        print(
            f'ASSETS DUMP: {len(data["buttons"])} buttons, {len(data["templates"])} templates, '
            f'{len(data["unparsed"])} unparsed'
        )
    elif mode == 'check':
        old = json.loads(Path(arg).read_text(encoding='utf-8'))
        new = parse_assets()
        errors = []
        for kind in ('buttons', 'templates'):
            for name in sorted(set(old[kind]) | set(new[kind])):
                if old[kind].get(name) != new[kind].get(name):
                    errors.append(f'{kind}:{name}')
        if errors:
            print('ASSETS: MISMATCH')
            for e in errors[:20]:
                print(' ', e)
            sys.exit(1)
        print(f'ASSETS: OK ({len(new["buttons"])} buttons, {len(new["templates"])} templates)')
    else:
        sys.exit(f'unknown mode: {mode}')


if __name__ == '__main__':
    main()
