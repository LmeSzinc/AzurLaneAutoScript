"""Extract the Bootswatch/Bootstrap values the SPA shell actually relies on.

Parses each minified bootswatch theme file and dumps the declarations of the
selectors the shell's CSS cascade exposes (buttons, form controls, tables,
alerts, text colors, spinner, body/a/hr, :root variables). Output is a JSON
per theme that the token-authoring step reads.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSS_DIR = ROOT / "webapp-tauri" / "public" / "css"
OUT = ROOT / "dev_tools" / "webui" / "theme-extract.json"

THEMES = ["default", "dark", "minty", "yeti", "sketchy"]

# selectors to extract, in precedence order (later definitions of the same
# normalized selector overwrite earlier ones, matching the cascade for
# same-specificity rules)
WANT = [
    ":root",
    "body",
    "a",
    "a:hover",
    "hr",
    "h1,h2,h3,h4,h5,h6",
    "h4",
    ".btn",
    ".btn:hover",
    ".btn:focus,.btn.focus",
    ".btn:disabled,.btn.disabled",
    ".btn-primary",
    ".btn-primary:hover",
    ".btn-primary:focus,.btn-primary.focus",
    ".btn-primary:disabled,.btn-primary.disabled",
    ".btn-primary:not(:disabled):not(.disabled):active,.btn-primary:not(:disabled):not(.disabled).active",
    ".btn-success",
    ".btn-success:hover",
    ".btn-success:focus,.btn-success.focus",
    ".btn-success:disabled,.btn-success.disabled",
    ".btn-success:not(:disabled):not(.disabled):active,.btn-success:not(:disabled):not(.disabled).active",
    ".btn-info",
    ".btn-info:hover",
    ".btn-info:focus,.btn-info.focus",
    ".btn-info:disabled,.btn-info.disabled",
    ".btn-info:not(:disabled):not(.disabled):active,.btn-info:not(:disabled):not(.disabled).active",
    ".btn-sm",
    ".form-control",
    ".form-control:focus",
    ".form-control:disabled,.form-control[readonly]",
    ".form-control-sm",
    ".form-check",
    ".form-check-input",
    ".table",
    ".table th,.table td",
    ".table thead th",
    ".table-sm th,.table-sm td",
    ".alert",
    ".alert-danger",
    ".text-muted",
    ".text-success",
    ".text-danger",
    ".spinner-border",
    ".spinner-border-sm",
]


def blocks(css: str):
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selector = " ".join(match.group(1).split()).strip()
        decls = {}
        for decl in match.group(2).split(";"):
            if ":" not in decl:
                continue
            prop, value = decl.split(":", 1)
            prop, value = prop.strip(), value.strip()
            if prop and value:
                decls[prop] = value
        yield selector, decls


def normalize(selector: str) -> str:
    # strip comments/media wrappers; keep a canonical ordering of comma parts
    selector = re.sub(r"/\*.*?\*/", "", selector, flags=re.S)
    selector = re.sub(r"@media[^{]*\{", "", selector)
    selector = re.sub(r"}", "", selector)
    parts = [p.strip() for p in selector.split(",") if p.strip()]
    return sorted(set(parts))


def main():
    want = {sel: normalize(sel) for sel in WANT}
    out = {}
    for theme in THEMES:
        css = (CSS_DIR / f"{theme}.min.css").read_text(encoding="utf-8")
        found = {}
        for selector, decls in blocks(css):
            parts = normalize(selector)
            if not parts:
                continue
            # Merge declarations across matching blocks in file order so the
            # theme's overrides win over the bundled Bootstrap core, exactly
            # like the browser cascade for same-specificity rules.
            for sel, wanted_parts in want.items():
                if set(wanted_parts) <= set(parts):
                    merged = dict(found.get(sel, {}))
                    merged.update(decls)
                    found[sel] = merged
        out[theme] = {sel: found[sel] for sel in WANT if sel in found}
        missing = [sel for sel in WANT if sel not in found]
        if missing:
            print(f"{theme}: missing {missing}")
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    for theme in THEMES:
        n = sum(len(v) for v in out[theme].values())
        print(f"{theme}: {len(out[theme])} selector blocks, {n} declarations")


if __name__ == "__main__":
    sys.exit(main())
