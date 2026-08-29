"""Phase 456 D1 gate: table-driven handle_stage_name == legacy if-chain.

The legacy reference is extracted from `git show HEAD:module/campaign/run.py`
(the committed pre-refactor code), the new implementation from the working
tree. Both run inside identical stubs over a per-event input matrix, and
(name, folder, overrides) outputs must match exactly.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, ".")

from module.config.config_manual import ManualConfig
from module.handler.fast_forward import map_files, to_map_file_name

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN = ROOT / 'campaign'


class ConfigStub:
    STAGE_LOOP_ALIAS = getattr(ManualConfig, 'STAGE_LOOP_ALIAS', {})

    def __init__(self, command='Event'):
        self.StopCondition_RunCount = 0
        self.StopCondition_MapAchievement = 'non_stop'
        self.StopCondition_OilLimit = 0
        self.Campaign_Name = ''
        self.task = SimpleNamespace(command=command)
        self.overrides = []

    def override(self, **kwargs):
        self.overrides.append(kwargs)
        return True

    def cross_get(self, keys, default=None):
        return default

    def cross_set(self, keys, value):
        return None

    def task_delay(self, minute=0):
        return None

    def task_stop(self):
        return None


def extract_method(source: str, name: str):
    """Return source text of a top-level class method (first class body match)."""
    tree = ast.parse(source)
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return ast.get_source_segment(source, node)
    raise KeyError(name)


def extract_functions(source: str, names: list[str]) -> dict[str, str]:
    tree = ast.parse(source)
    found = {}
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and node.name in names:
                found[node.name] = ast.get_source_segment(source, node)
    return found


def build_runner(source: str, method_names: list[str], extra_globals: dict):
    funcs = extract_functions(source, method_names)
    if 'handle_stage_name' not in funcs:
        raise RuntimeError('handle_stage_name not found')
    ns = dict(extra_globals)
    for _fname, fsrc in funcs.items():
        exec(fsrc, ns)
    return type('Runner', (), ns)


def run_case(runner, config, name, folder, mode='normal'):
    config.overrides = []
    result = runner.handle_stage_name(runner, name, folder, mode=mode)
    return result, list(config.overrides)


def iter_matrix():
    names = {'12-4', '7-2', 'd3', 'a1', 'b2', 'c1', 't1', 'ht1', 'sp1', 'vsp', 'esp',
             'asp', 'a.sp', 'y.sp', 'usp', 'iisp', 'μsp', 'lsp', '1sp', 'isp', 'isp1',
             'tp', 'e0', 'e01', 'th1', 'ts1', 'tss1', 'ysp', 'jjsp', 'sp', 'a2', 't2', 'd1', 'ht2'}
    folders = ['campaign_main', 'event_20201126_cn', 'event_20220324_cn',
               'event_20220818_cn', 'event_20221124_cn', 'event_20240425_cn',
               'event_20260417_cn', 'event_20211125_cn', 'event_20231026_cn', 'event_20241024_cn',
               'event_20250424_cn', 'event_20250724_cn', 'event_20250814_cn', 'event_20251023_cn',
               'event_20260326_cn', 'event_20260625_cn', 'war_archives_20230525_cn',
               'war_archives_20231026_cn', 'war_archives_20240725_cn', 'event_20200917_cn',
               'event_20230525_cn', 'war_archives_20200917_cn', 'event_20231123_cn',
               'event_20240725_cn', 'event_20240829_cn', 'event_20241121_cn', 'event_20230817_cn',
               'event_20240912_cn', 'event_20200507_cn']
    for folder in folders:
        for name in sorted(names):
            yield name, folder, 'normal'
    # a few hard-mode and GemsFarming command cases
    for name, folder in [('campaign_10_1', 'campaign_main'), ('d3', 'event_20250724_cn')]:
        yield name, folder, 'hard'
    yield '12-4', 'event_20250724_cn', 'normal'


def main():
    old_src = subprocess.run(
        ['git', 'show', 'HEAD:module/campaign/run.py'], capture_output=True, text=True, check=True
    ).stdout
    new_src = (ROOT / 'module/campaign/run.py').read_text(encoding='utf-8')

    legacy = build_runner(old_src, ['handle_stage_name'],
                          {'to_map_file_name': to_map_file_name, 'map_files': map_files})
    import random as _random

    from module.campaign.stage_meta import CHAPTER_CONVERT_REVERSE, load_stage_meta
    new = build_runner(new_src, ['handle_stage_name', '_override_condition'],
                       {'to_map_file_name': to_map_file_name, 'map_files': map_files,
                        'random': _random, 'load_stage_meta': load_stage_meta,
                        'CHAPTER_CONVERT_REVERSE': CHAPTER_CONVERT_REVERSE})

    cases = 0
    mismatches = []
    extra_achievements = [(name, folder, 'normal') for name, folder, mode in
                          [('d3', 'event_20240912_cn', 'normal'), ('a1', 'event_20240912_cn', 'normal')]]
    for name, folder, mode in list(iter_matrix()) + extra_achievements:
        for command in ('Event', 'GemsFarming'):
            old_cfg = ConfigStub(command=command)
            new_cfg = ConfigStub(command=command)
            if folder == 'event_20240912_cn' and command == 'Event':
                old_cfg.StopCondition_MapAchievement = 'threat_safe'
                new_cfg.StopCondition_MapAchievement = 'threat_safe'
            try:
                old_out = run_case(legacy, old_cfg, name, folder, mode)
            except Exception as e:
                old_out = ('<exception>', [repr(e)])
            try:
                new_out = run_case(new, new_cfg, name, folder, mode)
            except Exception as e:
                new_out = ('<exception>', [repr(e)])
            cases += 1
            if old_out != new_out:
                mismatches.append((name, folder, mode, command, old_out, new_out))

    if mismatches:
        print(f'STAGE_META: FAIL ({len(mismatches)}/{cases} cases differ)')
        for m in mismatches[:10]:
            print(' ', m)
        sys.exit(1)
    print(f'STAGE_META: OK ({cases} cases)')
    # meta.json sanity: every meta.json must be valid JSON with rules list
    metas = list(CAMPAIGN.rglob('meta.json'))
    for p in metas:
        data = json.loads(p.read_text(encoding='utf-8'))
        assert isinstance(data.get('rules'), list), p
    print(f'STAGE_META: {len(metas)} meta.json files valid')


if __name__ == '__main__':
    main()
