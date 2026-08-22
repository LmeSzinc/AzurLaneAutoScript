"""Phase 4C gate: regenerating all config artifacts must not introduce NEW tracked diffs.

Algorithm (do not alter):
1. snapshot tracked diff set: `git diff --name-only` + `git diff --cached --name-only`;
2. record current HEAD SHA;
3. run the exact same two calls as regenerate_config;
4. snapshot tracked diff set again; if the generator introduced any file not
   already dirty -> print diff and exit 1;
   otherwise print `CONFIG GENERATED: ZERO DRIFT` and exit 0.

This shape allows running the gate mid-step (the step's own source edits are
expected dirty); the invariant is that regeneration adds nothing new.

Tracked artifacts covered (for reporting):
module/config/argument/args.json, module/config/argument/menu.json,
module/config/config_generated.py, module/config/i18n/*.json,
config/deploy.template*.yaml, config/template.json, campaign/Readme.md
"""
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from module.config.config_updater import ConfigGenerator, ConfigUpdater


def tracked_diff_names() -> set[str]:
    names = set()
    for args in (['git', 'diff', '--name-only'], ['git', 'diff', '--cached', '--name-only']):
        out = subprocess.run(args, capture_output=True, text=True, check=True).stdout
        names.update(line for line in out.splitlines() if line.strip())
    return names


if __name__ == '__main__':
    head = subprocess.run(
        ['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True
    ).stdout.strip()
    print(f'verify_config_generated: baseline HEAD {head}')

    before = tracked_diff_names()
    ConfigGenerator().generate()
    ConfigUpdater().update_file('template', is_template=True)
    after = tracked_diff_names()

    new = sorted(after - before)
    if new:
        print('CONFIG GENERATED: DRIFT DETECTED')
        for name in new:
            print(name)
        sys.exit(1)
    print('CONFIG GENERATED: ZERO DRIFT')
