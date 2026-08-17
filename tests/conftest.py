"""Pytest root configuration.

The project is not installed as a package: `module.*` imports resolve from
the repo root (cwd / sys.path). Insert the root here so tests can import
the project regardless of how pytest is invoked.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
