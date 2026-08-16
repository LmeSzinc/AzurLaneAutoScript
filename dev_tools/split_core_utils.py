"""Split module/base/utils.py (1205 lines, god module) into module/core/*.

One-time refactoring tool for the code-organization-2026 proposal (P1.1).
Split plan (function -> target file, cross-file deps resolved):

    core/random.py   random_normal_distribution_int, random_rectangle_point,
                     random_rectangle_vector, random_rectangle_vector_opted,
                     random_line_segments, ensure_time
                     deps: core.geometry (area_limit, area_offset, area_size,
                           point_in_area, point_limit)
    core/geometry.py REGEX_NODE, ensure_int, area_offset, area_pad, limit_in,
                     area_limit, area_size, point_limit, point_in_area,
                     area_in_area, area_cross_area, float2str, point2str,
                     col2name, name2col, node2location, location2node,
                     xywh2xyxy, xyxy2xywh
    core/image.py    load_image, save_image, copy_image, crop, resize,
                     image_channel, image_size, image_paste, rgb2gray,
                     rgb2hsv, rgb2yuv, rgb2luma, get_bbox, get_bbox_reversed,
                     extract_letters, extract_white_letters, color_mapping,
                     image_left_strip, red_overlay_transparency,
                     ImageNotSupported
    core/color.py    get_color, color_similarity, color_similar,
                     color_similar_1d, color_similarity_2d, color_bar_percentage
                     deps: core.image (crop)

module/base/utils.py is rewritten as a compatibility re-export layer so the
existing `from module.base.utils import *` / explicit imports keep working.

Usage:
    python dev_tools/split_core_utils.py
    python dev_tools/smoke_import_all.py   # must stay 356/357 (+4 core)
"""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UTILS = ROOT / "module" / "base" / "utils.py"
CORE = ROOT / "module" / "core"

SPLIT = {
    "random.py": [
        "random_normal_distribution_int",
        "random_rectangle_point",
        "random_rectangle_vector",
        "random_rectangle_vector_opted",
        "random_line_segments",
        "ensure_time",
    ],
    "geometry.py": [
        "REGEX_NODE",
        "ensure_int",
        "area_offset",
        "area_pad",
        "limit_in",
        "area_limit",
        "area_size",
        "point_limit",
        "point_in_area",
        "area_in_area",
        "area_cross_area",
        "float2str",
        "point2str",
        "col2name",
        "name2col",
        "node2location",
        "location2node",
        "xywh2xyxy",
        "xyxy2xywh",
    ],
    "image.py": [
        "load_image",
        "save_image",
        "copy_image",
        "crop",
        "resize",
        "image_channel",
        "image_size",
        "image_paste",
        "rgb2gray",
        "rgb2hsv",
        "rgb2yuv",
        "rgb2luma",
        "get_bbox",
        "get_bbox_reversed",
        "extract_letters",
        "extract_white_letters",
        "color_mapping",
        "image_left_strip",
        "red_overlay_transparency",
        "ImageNotSupported",
    ],
    "color.py": [
        "get_color",
        "color_similarity",
        "color_similar",
        "color_similar_1d",
        "color_similarity_2d",
        "color_bar_percentage",
    ],
}

HEADERS = {
    "random.py": (
        "import random\n"
        "\n"
        "import numpy as np\n"
        "\n"
        "from module.core.geometry import area_limit, area_offset, area_size, point_in_area, point_limit\n"
    ),
    "geometry.py": "import re\n",
    "image.py": "import cv2\nimport numpy as np\nfrom PIL import Image\n",
    "color.py": "import cv2\nimport numpy as np\n\nfrom module.core.image import crop\n",
}


def main():
    src = UTILS.read_text(encoding="utf-8")
    tree = ast.parse(src)
    # name -> source segment
    segments = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            segments[node.name] = ast.get_source_segment(src, node)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            segments[node.targets[0].id] = ast.get_source_segment(src, node)

    # Verify split covers everything
    covered = {n for names in SPLIT.values() for n in names}
    missing = set(segments) - covered
    if missing:
        raise SystemExit(f"Uncovered top-level names: {sorted(missing)}")
    extra = covered - set(segments)
    if extra:
        raise SystemExit(f"Split names not found in source: {sorted(extra)}")

    # Write core modules
    CORE.mkdir(exist_ok=True)
    for fname, names in SPLIT.items():
        body = "\n\n\n".join(segments[n] for n in names)
        header = HEADERS[fname]
        content = header + "\n" + body + "\n"
        (CORE / fname).write_text(content, encoding="utf-8", newline="\n")
        print(f"wrote module/core/{fname} ({len(names)} symbols)")

    # Rewrite utils.py as re-export layer (module-level names preserved)
    reexports = [
        "import random\n",
        "\n",
        "import re\n",
        "\n",
        "import cv2\n",
        "import numpy as np\n",
        "from PIL import Image\n",
        "\n",
    ]
    for fname, names in SPLIT.items():
        mod = f"module.core.{fname[:-3]}"
        for n in names:
            reexports.append(f"from {mod} import {n}\n")
    layer = (
        "# Compatibility re-export layer (P1.1 refactor).\n"
        "# All symbols moved to module/core/*; keep this module so existing\n"
        "# `from module.base.utils import *` / explicit imports work unchanged.\n"
        "# Module-level names (cv2/np/Image/re/random) are re-exported too, as\n"
        "# 31 files import them from here (rope-expanded explicit imports).\n"
        "\n"
        + "".join(reexports)
    )
    UTILS.write_text(layer, encoding="utf-8", newline="\n")
    print(f"rewrote module/base/utils.py as re-export layer ({len(SPLIT)} source modules)")

    # Sanity: new modules parse and export exactly the split symbols
    for fname, names in SPLIT.items():
        mod = (CORE / fname).read_text(encoding="utf-8")
        t2 = ast.parse(mod)
        got = {n.name for n in t2.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        got |= {
            t.targets[0].id
            for t in t2.body
            if isinstance(t, ast.Assign) and len(t.targets) == 1 and isinstance(t.targets[0], ast.Name)
        }
        if got != set(names):
            raise SystemExit(f"module/core/{fname} symbol mismatch: got {sorted(got)} want {sorted(names)}")
    print("symbol check OK")


if __name__ == "__main__":
    main()
