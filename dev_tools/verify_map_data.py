"""Phase 4A gate: rebuilt (YAML) maps must equal their legacy semantic snapshot.

Usage:
    .venv\\Scripts\\python.exe dev_tools/verify_map_data.py <folder>
    .venv\\Scripts\\python.exe dev_tools/verify_map_data.py --all

For every converted map (YAML + fragment) the loader output is compared
against `.legacy_snapshot/<name>.snapshot.json` (recorded from the legacy
.py before conversion): map literals, per-grid code/weight/spawn flags,
ignore_prediction replay, Config namespace, Campaign method names and road
definitions. Any difference exits 1.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

from module.campaign.map_loader import _resolve_map, load_map, load_map_file

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN = ROOT / 'campaign'

CONFIG_NOISE = {'__module__', '__dict__', '__weakref__', '__doc__', '__annotations__'}


def grid_props(m):
    return {
        loca: {
            'str': m[loca].str,
            'weight': m[loca].weight,
            'is_spawn_point': m[loca].is_spawn_point,
        }
        for loca in m.grids
    }


def check_one(folder, name):
    errors = []
    loaded = load_map(folder, name)
    if loaded.source != 'json':
        return ['not converted (legacy source)']

    snap_path = CAMPAIGN / folder / '.legacy_snapshot' / f'{name}.snapshot.json'
    if not snap_path.exists():
        return [f'snapshot missing: {snap_path}']
    snap = json.loads(snap_path.read_text(encoding='utf-8'))

    # converter fidelity: committed yaml must equal the recorded legacy snapshot
    data = load_map_file(str(CAMPAIGN / folder / f'{name}.yaml'))
    for field in ('map', 'config_base', 'config', 'roads', 'selects', 'actions', 'extra_maps',
                  'imports', 'campaign_base_name', 'globals'):
        if data.get(field) != snap.get(field):
            errors.append(f'yaml field {field} differs from snapshot')

    reference = _resolve_map(folder, dict(snap['map']), snap.get('actions', []))

    if loaded.MAP.name != reference.name:
        errors.append(f'name: {loaded.MAP.name!r} != {reference.name!r}')
    if grid_props(loaded.MAP) != grid_props(reference):
        errors.append('grid props differ')
    if loaded.MAP._spawn_data != reference._spawn_data:
        errors.append('spawn_data differ')
    if loaded.MAP._map_data != reference._map_data:
        errors.append('map_data differ')
    if loaded.MAP._weight_data != reference._weight_data:
        errors.append('weight_data differ')
    if loaded.MAP._ignore_prediction != reference._ignore_prediction:
        errors.append('ignore_prediction differ')

    config_dict = {k: v for k, v in loaded.Config.__dict__.items() if k not in CONFIG_NOISE}
    if config_dict != snap['config']:
        errors.append('Config namespace differ')

    import types
    methods = {
        k for k, v in loaded.Campaign.__dict__.items()
        if isinstance(v, (types.FunctionType, staticmethod, classmethod))
    }
    if methods != set(snap['campaign_methods']):
        errors.append(f'Campaign methods differ: {sorted(methods)} vs {snap["campaign_methods"]}')

    return errors


def main():
    if len(sys.argv) != 2:
        sys.exit('usage: verify_map_data.py <folder> | --all')
    if sys.argv[1] == '--all':
        folders = sorted(p.name for p in CAMPAIGN.iterdir() if p.is_dir())
    else:
        folders = [sys.argv[1]]

    total, checked, failed = 0, 0, []
    skipped_count = 0
    for folder in folders:
        snap_dir = CAMPAIGN / folder / '.legacy_snapshot'
        if not snap_dir.exists():
            continue
        for snap in sorted(snap_dir.glob('*.snapshot.json')):
            total += 1
            name = snap.name[:-len('.snapshot.json')]
            errors = check_one(folder, name)
            if errors:
                failed.append((folder, name, errors))
            else:
                checked += 1
        skipped_file = snap_dir / 'skipped.txt'
        if skipped_file.exists():
            skipped_count += sum(1 for _ in skipped_file.read_text(encoding='utf-8').splitlines() if _.strip())

    print(f'MAP DATA: checked {checked}/{total} maps, {skipped_count} skipped')
    if failed:
        print(f'MAP DATA: FAIL ({len(failed)} maps)')
        for folder, name, errors in failed[:10]:
            print(f'  {folder}/{name}: {errors[:3]}')
        sys.exit(1)
    print('MAP DATA: OK')


if __name__ == '__main__':
    main()
