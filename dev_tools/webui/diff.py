"""Pixel-diff two screenshot trees (baseline vs new) to measure visual fidelity.

Usage:
  python dev_tools/webui/diff.py <dir-a> <dir-b> [--threshold 0.02]

For each <theme>/<route>.png pair it prints the share of pixels that differ
and the mean per-channel absolute error, and writes a per-pair diff heatmap
into <dir-b>/_diff/<theme>-<route>-diff.png. Exit code 1 if any pair exceeds
the threshold share of differing pixels.
"""

import sys
from pathlib import Path

from PIL import Image, ImageChops


def compare(a: Path, b: Path):
    ia = Image.open(a).convert("RGB")
    ib = Image.open(b).convert("RGB")
    if ia.size != ib.size:
        return None, f"size mismatch {ia.size} vs {ib.size}"
    diff = ImageChops.difference(ia, ib)
    pixels = diff.size[0] * diff.size[1]
    data = diff.get_flattened_data() if hasattr(diff, "get_flattened_data") else diff.getdata()
    changed = sum(1 for p in data if p != (0, 0, 0))
    mean_err = sum(sum(p) for p in data) / (pixels * 3)
    heat = diff.convert("L").point(lambda v: 255 if v else 0)
    heatmap = Image.new("RGB", ia.size)
    heatmap.paste(Image.composite(Image.new("RGB", ia.size, (255, 0, 255)), ib, heat), (0, 0))
    return (changed / pixels, mean_err), heatmap


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        sys.exit(2)
    threshold = 0.02
    if "--threshold" in sys.argv:
        threshold = float(sys.argv[sys.argv.index("--threshold") + 1])
    dir_a, dir_b = Path(args[0]), Path(args[1])
    failed = False
    out_dir = dir_b / "_diff"
    out_dir.mkdir(parents=True, exist_ok=True)
    for fa in sorted(dir_a.rglob("*.png")):
        rel = fa.relative_to(dir_a)
        fb = dir_b / rel
        if not fb.exists():
            print(f"missing {rel}")
            failed = True
            continue
        result, heatmap = compare(fa, fb)
        if result is None:
            print(f"{rel}: {heatmap}")
            failed = True
            continue
        share, mean_err = result
        status = "OK " if share <= threshold else "DIFF"
        if share > threshold:
            failed = True
        print(f"{status} {rel}: {share*100:6.2f}% pixels differ, mean channel err {mean_err:5.2f}")
        heatmap.save(out_dir / f"{'-'.join(rel.parts).replace('.png', '')}-diff.png")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
