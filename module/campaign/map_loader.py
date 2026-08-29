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
    return importlib.import_module('campaign.' + base).Config


def _folder_campaign_base(folder):
    cb = os.path.join(_CAMPAIGN, folder, 'campaign_base.py')
    if os.path.exists(cb):
        return importlib.import_module('.' + 'campaign_base', f'campaign.{folder}').CampaignBase
    return importlib.import_module('module.campaign.campaign_base').CampaignBase


def _load_data(folder, name, json_path):
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    MAP = CampaignMap.from_data(data['map'])

    # config: full class namespace, optional base chain
    Config = type('Config', (_load_config(folder, data.get('config_base')),), data['config'])

    # roads -> RoadGrids objects, injected into fragment namespace
    flatten_names = {}
    for loca, grid in MAP.grids.items():
        flatten_names[chr(loca[0] + 65) + str(loca[1] + 1)] = grid  # A1..Z99
    ns = {'MAP': MAP, 'Config': Config, 'RoadGrids': RoadGrids, 'SelectedGrids': SelectedGrids,
          'logger': logger, 'CampaignMap': CampaignMap, **flatten_names}
    for road_name, nodes in data.get('roads', {}).items():
        ns[f'road_{road_name}'] = RoadGrids([MAP[node2location(n)] for n in nodes])
    for action in data.get('actions', []):
        getattr(MAP, action['call'])(*action['args'], **action['kwargs'])

    # fragment: only `class Campaign(CampaignBase): ...`, no imports,
    # every name is provided by the namespace above.
    ns['CampaignBase'] = _folder_campaign_base(folder)
    frag_path = os.path.join(_CAMPAIGN, folder, f'{name}.py')
    with open(frag_path, encoding='utf-8') as f:
        source = f.read()
    exec(compile(source, frag_path, 'exec'), ns)  # noqa: S102 - own data-driven fragment
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
