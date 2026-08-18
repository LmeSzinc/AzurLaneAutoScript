"""Import smoke test: walk and import every module under `module/` (and top-level entry files).

Usage:
    python .qoder/smoke_import_all.py [--json out.json]

Exit code 0 if every module imports; 1 if any fails (failures printed + saved).
This is the baseline gate for refactoring work: before/after diffs of the
failure list must be identical (or strictly shrink).

Notes:
- `module.webui.api` imports fastapi etc.; all dependencies are installed in .venv.
- Importing some modules starts background threads (e.g. ocr rpc is NOT started
  on import; logger handlers are file-less until set_file_logger). Importing
  module.device.device pulls adbutils/uiautomator2, which is fine offline.
- `campaign/` generated code is intentionally excluded (ruff excludes it too).
- `submodule/` vendored bridges are excluded (ruff excludes them too).
"""

import argparse
import importlib
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

EXCLUDED_TOP = {"campaign", "submodule", "webapp"}


def iter_module_names():
    """Yield dotted module names for every .py under module/, walking the
    filesystem (module/ is a namespace package without __init__.py, so
    pkgutil.walk_packages cannot recurse into it)."""
    for py in sorted((ROOT / "module").rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        rel = py.relative_to(ROOT / "module")
        top = rel.parts[0]
        if top in EXCLUDED_TOP:
            continue
        if rel.name == "__init__.py":
            name = "module." + ".".join(rel.parts[:-1])
        else:
            name = "module." + ".".join((*rel.parts[:-1], rel.stem))
        yield name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=None, help="Write results to this JSON file")
    parser.add_argument("--top", action="store_true", help="Also import top-level entries (alas.py, gui.py)")
    args = parser.parse_args()

    results = {}
    failed = []
    count = 0
    for name in iter_module_names():
        count += 1
        try:
            importlib.import_module(name)
            results[name] = "ok"
        except Exception as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            results[name] = f"FAIL: {e!r}"
            failed.append((name, str(e), tb))

    if args.top:
        for entry in ("alas", "gui"):
            try:
                importlib.import_module(entry)
                results[f"<top> {entry}"] = "ok"
            except Exception as e:
                tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
                results[f"<top> {entry}"] = f"FAIL: {e!r}"
                failed.append((f"<top> {entry}", str(e), tb))

    ok = count - len(failed)
    print(f"Imported {ok}/{count} modules" + (f" (+{len([f for f in failed if f[0].startswith('<top>')])} top-level)" if args.top else ""))
    for name, err, _ in failed:
        print(f"  FAIL {name}: {err}")

    if args.json:
        out = {
            "count": count,
            "ok": ok,
            "failed": [{"module": n, "error": e, "traceback": tb} for n, e, tb in failed],
        }
        Path(args.json).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved to {args.json}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
