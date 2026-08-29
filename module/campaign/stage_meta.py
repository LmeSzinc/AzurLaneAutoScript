"""Per-event stage-name normalization data (Phase 456 D1).

Each `campaign/<folder>/meta.json` carries an ordered rule list that mirrors
the legacy hard-coded if-chain in handle_stage_name. Rules are applied in
order; see dev_tools/verify_stage_meta.py for the equivalence gate.
"""
from __future__ import annotations

import json
import os
from functools import cache
from typing import Any

_META_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'campaign')

# Legacy chapter mapping tables (run.py convert#1/convert#2).
CHAPTER_CONVERT = {
    'a1': 't1', 'a2': 't2', 'a3': 't3', 'b1': 't4', 'b2': 't5', 'b3': 't6',
    'c1': 'ht1', 'c2': 'ht2', 'c3': 'ht3', 'd1': 'ht4', 'd2': 'ht5', 'd3': 'ht6',
}
CHAPTER_CONVERT_REVERSE = {v: k for k, v in CHAPTER_CONVERT.items()}
CHAPTER_CONVERT_STAGE = {
    'a1': 't1', 'a2': 't2', 'a3': 't3', 'a4': 't4', 'a5': 't5', 'a6': 't6',
    'sp1': 't1', 'sp2': 't2', 'sp3': 't3', 'sp4': 't4', 'sp5': 't5', 'sp6': 't6',
}


@cache
def load_stage_meta(folder: str) -> dict[str, Any]:
    path = os.path.join(_META_DIR, folder, 'meta.json')
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        return json.load(f)
