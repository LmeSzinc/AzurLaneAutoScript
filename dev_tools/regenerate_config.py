"""Single entry to regenerate all config artifacts (Phase 4C).
Usage: uv run python dev_tools/regenerate_config.py
"""
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from module.config.config_updater import ConfigGenerator, ConfigUpdater

if __name__ == '__main__':
    ConfigGenerator().generate()
    ConfigUpdater().update_file('template', is_template=True)
