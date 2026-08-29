"""Phase 456 transformer: extract declarative battle patterns from fragments.

For every converted map fragment:
- battle methods matching a known pattern (module/campaign/battle_patterns.py)
  become `battles: {name: spec}` in the map YAML; the method def is removed
  from the fragment. Canonical equality is asserted before extraction.
- ENEMY_FILTER class assigns equal to the resolved base-class default are
  removed (the attribute is inherited).

Snapshots gain `battles` and `battle_bodies` (pre-extraction method sources)
so verify_map_data can re-assert structural equality.

Usage: .venv\\Scripts\\python.exe dev_tools/extract_battle_patterns.py [folder]
"""
import ast
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")


from module.campaign.battle_patterns import canonical_source, match_body
from module.campaign.map_loader import dump_map_file, load_map, load_map_file

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN = ROOT / 'campaign'


def _is_shell_fragment(fragment_text: str) -> bool:
    try:
        tree = ast.parse(fragment_text)
    except Exception:
        return False
    return (len(tree.body) == 1 and isinstance(tree.body[0], ast.ClassDef)
            and tree.body[0].name == 'Campaign'
            and len(tree.body[0].body) == 1 and isinstance(tree.body[0].body[0], ast.Pass))


def transform(folder_path: Path):
    changed = 0
    for yp in sorted(folder_path.glob('*.yaml')):
        name = yp.stem
        py = folder_path / f'{name}.py'
        if not py.exists():
            continue
        data = load_map_file(str(yp))
        tree = ast.parse(py.read_text(encoding='utf-8'))

        # resolve the base class for the ENEMY_FILTER default comparison
        loaded = load_map(folder_path.name, name)
        base_cls = loaded.Campaign.__mro__[1] if len(loaded.Campaign.__mro__) > 1 else None
        base_filter = getattr(base_cls, 'ENEMY_FILTER', None)

        battles: dict[str, dict] = {}
        bodies: dict[str, str] = {}
        removed_nodes: list[ast.stmt] = []
        for cls in [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Campaign']:
            for node in cls.body:
                if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                        and isinstance(node.targets[0], ast.Name) \
                        and node.targets[0].id == 'ENEMY_FILTER':
                    value = ast.literal_eval(node.value)
                    if base_filter is not None and value == base_filter:
                        removed_nodes.append(node)
                    continue
                if isinstance(node, ast.FunctionDef) and not node.decorator_list:
                    spec = match_body(node.body)
                    if spec is None:
                        continue
                    canonical = canonical_source(node.name, spec)
                    original = ast.unparse(node)
                    if canonical != original:
                        print(f'  CANONICAL MISMATCH {folder_path.name}/{name}.{node.name}')
                        print(f'    original: {original[:150]}')
                        print(f'    canonical: {canonical[:150]}')
                        sys.exit(1)
                    battles[node.name] = spec
                    bodies[node.name] = original
                    removed_nodes.append(node)
        if not removed_nodes and not battles:
            continue
        # rebuild fragment via ast.unparse (pass body when everything extracted)
        removed = {id(n) for n in removed_nodes}
        rebuilt: list[ast.stmt] = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == 'Campaign':
                kept = [n for n in node.body if id(n) not in removed] or [ast.Pass()]
                new_cls = ast.ClassDef(
                    name=node.name, bases=node.bases, keywords=node.keywords,
                    body=kept, decorator_list=[],
                )
                rebuilt.append(new_cls)
            else:
                rebuilt.append(node)
        fragment_text = '\n\n'.join(
            ast.unparse(ast.fix_missing_locations(n)) for n in rebuilt
        ).rstrip() + '\n'
        if _is_shell_fragment(fragment_text):
            # no hand-written logic left: the loader synthesizes the class
            py.unlink(missing_ok=True)
        else:
            py.write_text(fragment_text, encoding='utf-8', newline='\n')
        # update yaml + snapshot
        data['battles'] = battles
        yp.write_text(dump_map_file(json.loads(json.dumps(data))), encoding='utf-8', newline='\n')
        snap_path = folder_path / '.legacy_snapshot' / f'{name}.snapshot.json'
        snap = json.loads(snap_path.read_text(encoding='utf-8'))
        snap['battles'] = battles
        snap['battle_bodies'] = bodies
        snap_path.write_text(
            json.dumps(snap, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n'
        )
        changed += 1
    return changed


def main():
    folders = [sys.argv[1]] if len(sys.argv) > 1 else sorted(
        p.name for p in CAMPAIGN.iterdir() if p.is_dir()
    )
    total = 0
    for folder in folders:
        folder_path = CAMPAIGN / folder
        if not (folder_path / '.legacy_snapshot').exists():
            continue
        n = transform(folder_path)
        if n:
            print(f'{folder}: {n} maps transformed')
        total += n
    print('TOTAL transformed:', total)


if __name__ == '__main__':
    main()
