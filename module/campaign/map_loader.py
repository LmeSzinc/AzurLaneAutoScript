"""Phase 4A: unified map loading. JSON first, legacy .py fallback.

`load_map(folder, name)` returns a LoadedMap mirroring the legacy module
namespace (MAP / Config / Campaign), so campaign run/hard and gems_farming
(`self.module.Campaign`) keep working unchanged.
"""
from __future__ import annotations

import importlib
import json
import os
from functools import lru_cache

from module.base.utils import node2location
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids

_CAMPAIGN = os.path.join(os.path.dirname(__file__), '..', '..', 'campaign')


class LoadedMap:
    """Mirrors the legacy module namespace: MAP / Config / Campaign."""

    def __init__(self, MAP, Config, Campaign, source: str):
        self.MAP = MAP
        self.Config = Config
        self.Campaign = Campaign
        self.source = source


def _load_config(folder, base):
    """Resolve Config base class: json map if converted, else legacy module.

    `base` is either a bare module name in `folder`, or 'subdir.module'
    (cross-folder imports like campaign_hard -> campaign_main.campaign_14_base).
    """
    if base is None:
        return object
    parts = base.split('.')
    if len(parts) > 1:
        base_folder, base_module = '/'.join(parts[:-1]), parts[-1]
    else:
        base_folder, base_module = folder, base
    json_path = os.path.join(_CAMPAIGN, base_folder, f'{base_module}.json')
    if os.path.exists(json_path):
        return load_map(base_folder, base_module).Config
    if len(parts) > 1:
        return importlib.import_module('campaign.' + base).Config
    try:
        return importlib.import_module(f'campaign.{folder}.{base}').Config
    except ModuleNotFoundError:
        return importlib.import_module('campaign.' + base).Config


def _folder_campaign_base(folder):
    cb = os.path.join(_CAMPAIGN, folder, 'campaign_base.py')
    if os.path.exists(cb):
        return importlib.import_module('.' + 'campaign_base', f'campaign.{folder}').CampaignBase
    return importlib.import_module('module.campaign.campaign_base').CampaignBase


def _resolve_value(folder, value):
    """Resolve {'__ref__': '<module>.<attr>'} references produced by the converter."""
    if isinstance(value, dict) and '__ref__' in value:
        parts = value['__ref__'].split('.')
        module, attr = '.'.join(parts[:-1]), parts[-1]
        if module:
            mod = None
            for prefix in (f'campaign.{folder}.', 'campaign.', ''):
                try:
                    mod = importlib.import_module(prefix + module)
                    break
                except ModuleNotFoundError:
                    continue
            if mod is None:
                raise ImportError(f'cannot resolve ref module: {module}')
        else:
            mod = None
        return getattr(mod, attr)
    return value


def _resolve_action_arg(m, value):
    """Grid-name strings ('D5') become grid objects, matching legacy flatten vars."""
    if isinstance(value, str) and value and value[0].isalpha() and value[1:].isdigit():
        return m[node2location(value)]
    return value


def _has_grid_marker(value):
    if isinstance(value, dict):
        return '__grid__' in value or '__tuple__' in value
    if isinstance(value, list):
        return any(_has_grid_marker(e) for e in value)
    return False


def _resolve_grid_value(m, value):
    """{'__grid__'/'__tuple__'} markers -> grid objects, preserving List/Tuple shape."""
    if isinstance(value, dict) and '__grid__' in value:
        return m[node2location(value['__grid__'])]
    if isinstance(value, dict) and '__tuple__' in value:
        return tuple(_resolve_grid_value(m, e) for e in value['__tuple__'])
    if isinstance(value, list):
        return [_resolve_grid_value(m, e) for e in value]
    return value


def _resolve_map(folder, attrs, actions):
    data = {'name': attrs.pop('name', None)}
    for key, value in attrs.items():
        data[key] = _resolve_value(folder, value)
    # grid-marker attrs need the map instance; apply after from_data so the
    # setters resolve names against the built grids.
    grid_attrs = {k: v for k, v in data.items() if _has_grid_marker(v)}
    m = CampaignMap.from_data({k: v for k, v in data.items() if k not in grid_attrs})
    for key, value in grid_attrs.items():
        setattr(m, key, _resolve_grid_value(m, value))
    for action in actions:
        args = [_resolve_action_arg(m, a) for a in action['args']]
        kwargs = {k: _resolve_action_arg(m, v) for k, v in action['kwargs'].items()}
        getattr(m, action['call'])(*args, **kwargs)
    return m


def _load_data(folder, name, json_path):
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    MAP = _resolve_map(folder, data['map'], data.get('actions', []))

    # config: full class namespace, optional base chain
    Config = type('Config', (_load_config(folder, data.get('config_base')),), data['config'])

    # roads (grouped) and flat SelectedGrids, injected into fragment namespace
    flatten_names = {}
    for loca, grid in MAP.grids.items():
        flatten_names[chr(loca[0] + 65) + str(loca[1] + 1)] = grid  # A1..Z99
    ns = {'MAP': MAP, 'Config': Config, 'RoadGrids': RoadGrids, 'SelectedGrids': SelectedGrids,
          'logger': logger, 'CampaignMap': CampaignMap, **flatten_names}

    def _road_grids(groups):
        grid_groups = [[MAP[node2location(n)] for n in group] for group in groups]
        return RoadGrids([group if len(group) > 1 else group[0] for group in grid_groups])

    def _eval_road_expr(expr, memo):
        if 'roadgrids' in expr:
            return _road_grids(expr['roadgrids'])
        if 'combine' in expr:
            return _eval_road_expr(expr['combine'][0], memo).combine(
                _eval_road_expr(expr['combine'][1], memo)
            )
        if 'ref' in expr:
            return memo[expr['ref']]
        if 'list' in expr:
            return [_eval_road_expr(e, memo) for e in expr['list']]
        raise ValueError(f'bad road expr: {expr}')

    for road_name, expr in data.get('roads', {}).items():
        ns[road_name] = _eval_road_expr(expr, ns)
    for sel_name, nodes in data.get('selects', {}).items():
        ns[sel_name] = SelectedGrids([MAP[node2location(n)] for n in nodes])
    for extra_name, extra in data.get('extra_maps', {}).items():
        ns[extra_name] = _resolve_map(folder, dict(extra['attrs']), extra.get('actions', []))
    # names imported by the legacy file (e.g. EventGrid/W15GridInfo) resolved
    # for class-level references in the fragment
    for alias, target in data.get('imports', {}).items():
        ns[alias] = _resolve_value(folder, {'__ref__': target})

    # fragment: only `class Campaign(CampaignBase): ...`, no imports,
    # every name is provided by the namespace above.
    ns['CampaignBase'] = _folder_campaign_base(folder)
    frag_path = os.path.join(_CAMPAIGN, folder, f'{name}.py')
    with open(frag_path, encoding='utf-8') as f:
        source = f.read()
    exec(compile(source, frag_path, 'exec'), ns)
    Campaign = ns['Campaign']
    Campaign.MAP = MAP
    return LoadedMap(MAP, Config, Campaign, 'json')


@lru_cache(maxsize=2048)
def load_map(folder: str, name: str) -> LoadedMap:
    json_path = os.path.join(_CAMPAIGN, folder, f'{name}.json')
    if os.path.exists(json_path):
        return _load_data(folder, name, json_path)
    module = importlib.import_module('.' + name, f'campaign.{folder}')  # legacy fallback
    return LoadedMap(module.MAP, module.Config, module.Campaign, 'legacy')
