"""Phase 4C gate: regenerating all config artifacts must leave tracked files unchanged.

Algorithm (do not alter):
1. `git diff --name-only` + `git diff --cached --name-only` non-empty -> error exit;
2. record current HEAD SHA;
3. run the exact same two calls as regenerate_config;
4. tracked diffs non-empty -> print diff and exit 1;
   empty -> print `CONFIG GENERATED: ZERO DRIFT` and exit 0.

Tracked artifacts covered (for reporting; the gate itself is git diff):
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


def git_dirty() -> str:
    staged = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'], capture_output=True, text=True, check=True
    ).stdout
    unstaged = subprocess.run(
        ['git', 'diff', '--name-only'], capture_output=True, text=True, check=True
    ).stdout
    return (staged + unstaged).strip()


if __name__ == '__main__':
    before = git_dirty()
    if before:
        print('verify_config_generated: tracked files dirty, commit first:')
        print(before)
        sys.exit(1)

    head = subprocess.run(
        ['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True
    ).stdout.strip()
    print(f'verify_config_generated: baseline HEAD {head}')

    ConfigGenerator().generate()
    ConfigUpdater().update_file('template', is_template=True)

    after = git_dirty()
    if after:
        print('CONFIG GENERATED: DRIFT DETECTED')
        print(after)
        sys.exit(1)
    print('CONFIG GENERATED: ZERO DRIFT')
