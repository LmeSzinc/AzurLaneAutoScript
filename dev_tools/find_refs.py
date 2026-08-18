"""
Find all references to a Python symbol across the repository.

Used as a double-check before deleting supposedly dead code (cleanup
phase 3): a symbol is safe to delete only when it has a single
reference -- its own definition site. Unlike rope's occurrences API
(which is scoped to one module) this walks every .py file in the tree,
including campaign/, config/ and submodule/, and also reports string
literals containing the name (task registries reference classes by
string, e.g. `"GemsFarming"` in module/tasks/registry.py).

Usage:
    python dev_tools/find_refs.py past_time
    python dev_tools/find_refs.py --batch symbols.txt   # one symbol per line
    python dev_tools/find_refs.py --json past_time      # machine-readable
"""
import argparse
import ast
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {
    ".venv",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".pnpm-store",
    ".qoder",
    ".ropeproject",
    "node_modules",
    "webapp-tauri",
    "__pycache__",
}


def iter_py_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return files


def collect_index() -> tuple[dict[str, list[dict]], list[dict]]:
    """Return (code sites by symbol, all string literal sites)."""
    index: dict[str, list[dict]] = defaultdict(list)
    str_sites: list[dict] = []
    for path in iter_py_files():
        try:
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text)
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        lines = text.splitlines()
        rel = str(path.relative_to(ROOT)).replace("\\", "/")

        def site(kind: str, node, name: str, *, rel: str = rel, lines: list[str] = lines) -> dict:
            lineno = getattr(node, "lineno", 0)
            return {
                "kind": kind,
                "file": rel,
                "line": lineno,
                "text": lines[lineno - 1].strip() if 0 < lineno <= len(lines) else "",
            }

        for node in ast.walk(tree):
            name = None
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name, kind = node.name, "def"
            elif isinstance(node, ast.ClassDef):
                name, kind = node.name, "class"
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                name, kind = node.id, "ref"
            elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                name, kind = node.id, "assign"
            elif isinstance(node, ast.Attribute) and node.attr.isidentifier():
                name, kind = node.attr, "attr"
            elif isinstance(node, ast.alias) and node.name:
                name, kind = node.name.split(".")[-1], "import"
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                str_sites.append(site("str", node, node.value))
                continue
            if name:
                index[name].append(site(kind, node, name))
    return index, str_sites


def query(name: str, index, str_sites) -> list[dict]:
    sites = list(index.get(name, []))
    word = re.compile(rf"\b{re.escape(name)}\b")
    sites += [s for s in str_sites if word.search(s["text"])]
    return sites


def format_report(name: str, sites: list[dict]) -> str:
    by_file: dict[str, list[dict]] = defaultdict(list)
    for site in sites:
        by_file[site["file"]].append(site)

    out = [f"`{name}` -- {len(sites)} site(s) in {len(by_file)} file(s)"]
    kinds = defaultdict(int)
    for site in sites:
        kinds[site["kind"]] += 1
    out.append("kinds: " + ", ".join(f"{k}={v}" for k, v in sorted(kinds.items())))
    for file in sorted(by_file):
        for site in by_file[file]:
            out.append(f"  {site['file']}:{site['line']}  [{site['kind']}] {site['text'][:100]}")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("symbols", nargs="*", help="symbol names to search")
    parser.add_argument("--batch", help="file with one symbol per line")
    parser.add_argument("--json", action="store_true", help="output JSON")
    args = parser.parse_args()

    symbols = list(args.symbols)
    if args.batch:
        symbols += [line.strip() for line in Path(args.batch).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if not symbols:
        parser.error("provide at least one symbol or --batch")

    index, str_sites = collect_index()

    if args.json:
        payload = {name: query(name, index, str_sites) for name in symbols}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    for name in symbols:
        print(format_report(name, query(name, index, str_sites)))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
