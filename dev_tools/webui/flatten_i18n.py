"""Standalone i18n flattening for the webui mock server.

Replicates module.webui.lang.reload()'s deep_iter(read_file(...), depth=3)
flattening without importing the ALAS package (so it can run in any
environment). Output: a flat {"A.B.C": "text"} JSON for the mock server.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def deep_iter_depth3(data):
    """Yields (key_path, value) for every depth-3 leaf, like deep_iter(data, depth=3)."""
    if not isinstance(data, dict):
        return
    for k1, v1 in data.items():
        if not isinstance(v1, dict):
            continue
        for k2, v2 in v1.items():
            if not isinstance(v2, dict):
                continue
            for k3, v3 in v2.items():
                yield [k1, k2, k3], v3


def main():
    lang = sys.argv[1] if len(sys.argv) > 1 else "zh-CN"
    src = ROOT / "module" / "config" / "i18n" / f"{lang}.json"
    out = ROOT / "dev_tools" / "webui" / f"mock-i18n-{lang}.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    flat = {".".join(path): str(value) for path, value in deep_iter_depth3(data)}
    out.write_text(json.dumps(flat, ensure_ascii=False), encoding="utf-8")
    print(f"{src} -> {out} ({len(flat)} keys)")


if __name__ == "__main__":
    main()
