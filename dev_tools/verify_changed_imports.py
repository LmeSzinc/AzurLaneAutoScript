"""Delivery gate: import every changed .py module individually (P1-P2 final check).

For each .py file changed on the refactor branch (vs master), derive its
module name and import it in a fresh interpreter. This catches missing
symbols, broken relative imports and runtime import errors that a single
combined smoke run may mask (e.g. import-order dependence).

Known pre-existing environment failure (pkg_resources missing) is filtered
with the same allowlist as smoke_import_all.py.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Pre-existing environment failures (verified identical on master):
# - module.handler.login imports uiautomator2 directly (not via the
#   module.device.pkg_resources patch chain), so it hits the real
#   pkg_resources missing from this uv env on Python 3.13.
ALLOWED_FAILURES = {"module.handler.login"}


def changed_py_files():
    out = subprocess.run(
        ["git", "diff", "--name-only", "master...HEAD"], capture_output=True, text=True, check=True
    ).stdout
    for line in out.strip().splitlines():
        if line.endswith(".py"):
            yield line


def module_name_for(path: str) -> str | None:
    """module/x/y.py -> module.x.y; skip non-module files (dev_tools, top-level)."""
    p = Path(path)
    parts = p.parts
    if parts[0] == "module":
        if p.name == "__init__.py":
            return "module." + ".".join(parts[1:-1])
        return "module." + ".".join((*parts[1:-1], p.stem))
    return None


def main():
    failures = []
    total = 0
    checked = 0
    for path in changed_py_files():
        total += 1
        name = module_name_for(path)
        if name is None:
            continue
        # Files that are only re-export layers get imported transitively anyway;
        # skip none — import everything under module/.
        checked += 1
        code = (
            f"import sys; sys.path.insert(0, {str(ROOT)!r});\n"
            f"import {name}\n"
            f"print('OK {name}')\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, timeout=120
        )
        if proc.returncode != 0:
            err = proc.stderr.strip().splitlines()
            err = [line for line in err if "Traceback" not in line and 'File "' not in line and "    " not in line]
            failures.append((name, " | ".join(err[-3:])))

    print(f"changed .py files: {total}, importable modules checked: {checked}")
    print(f"failures: {len(failures)}")
    real = []
    for name, err in failures:
        if name in ALLOWED_FAILURES:
            print(f"  ALLOWED {name}: {err}")
        else:
            real.append((name, err))
            print(f"  FAIL {name}: {err}")
    if real:
        print(f"UNEXPECTED FAILURES: {len(real)}")
        sys.exit(1)
    print("DELIVERY IMPORT GATE PASSED")


if __name__ == "__main__":
    main()
