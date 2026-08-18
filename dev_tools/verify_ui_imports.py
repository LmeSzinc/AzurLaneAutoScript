"""Verify module.ui imports cleanly after P2.2 bridge refactor."""

import sys

sys.path.insert(0, ".")

import module.ui.navbar
import module.ui.page
import module.ui.ui  # noqa: F401

print("page.py / ui.py / navbar.py imports OK")

import module.ui.page as p

pages = [n for n in dir(p) if n.startswith("page_")]
print(f"page objects: {len(pages)}")
missing = [n for n in pages if not hasattr(p, n)]
print(f"missing: {missing if missing else 'NONE'}")
