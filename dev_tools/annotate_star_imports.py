"""Annotate intentional star imports with `# noqa: F403` (P1.2).

Background: pyproject.toml currently ignores F403/F405 globally
("star import, used in legacy module.base.utils" / "name may be undefined
from star import"). The codebase deliberately uses star imports in two
patterns:

1. data-bundle imports: `from module.X.assets import *` (148 sites) --
   assets.py files are button/template data bundles consumed via `*`.
2. re-export facades: `from module.config.utils import *` etc. (16 sites
   under module/, 3 generated campaign files, 2 vendored submodule files).

This script rewrites every star import line to carry an explicit
`# noqa: F403 (data-bundle star import)` / `# noqa: F403 (re-export facade)`
annotation so the global ignore can be removed later and intent is
documented at each site. Lines are only rewritten if they do not already
carry a noqa comment. Idempotent: safe to run twice.

Excluded: campaign/ generated code (ruff-excluded anyway) and submodule/
vendored bridges are skipped by default; pass --all to include them.
"""

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAR_RE = re.compile(r"^(\s*)(from [\w.]+ import \*)(\s*#.*)?$")
EXCLUDED_TOPS = {"campaign", "submodule"}


def annotate(py: Path, include_all: bool, dry_run: bool) -> list[str]:
    if not include_all and py.parts[0] in EXCLUDED_TOPS:
        return []
    src = py.read_text(encoding="utf-8")
    lines = src.split("\n")
    changed = []
    for i, line in enumerate(lines):
        m = STAR_RE.match(line)
        if not m:
            continue
        if "noqa" in (m.group(3) or ""):
            continue
        indent, stmt, _ = m.groups()
        if "assets" in stmt:
            tag = "data-bundle star import"
        else:
            tag = "re-export facade"
        lines[i] = f"{indent}{stmt}  # noqa: F403  ({tag})"
        changed.append(f"  {py}:{i + 1}: {stmt} -> {tag}")
    if changed and not dry_run:
        py.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Also annotate campaign/ and submodule/")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    total = []
    for py in sorted(ROOT.rglob("*.py")):
        if any(x in py.parts for x in ("__pycache__", ".venv", "node_modules", ".pnpm-store", "webapp-tauri", ".git")):
            continue
        # Match against the repo-relative path so the top-level exclusion works
        rel = py.relative_to(ROOT)
        if not args.all and rel.parts[0] in EXCLUDED_TOPS:
            continue
        total += annotate(py, include_all=args.all, dry_run=args.dry_run)
    print("\n".join(total) if total else "(nothing to change)")
    print(f"\n{len(total)} star import lines annotated" + (" (dry run)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
