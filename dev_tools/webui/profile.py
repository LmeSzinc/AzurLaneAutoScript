"""Profile where two screenshots differ: per row/column band diff share.

Usage: python dev_tools/webui/profile.py <img-a> <img-b> [bands]
Prints the fraction of differing pixels in each horizontal (row) band and
vertical (column) band, so layout regressions can be localized without
viewing the images.
"""

import sys
from pathlib import Path

from PIL import Image, ImageChops


def main():
    a, b = Path(sys.argv[1]), Path(sys.argv[2])
    bands = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    ia = Image.open(a).convert("RGB")
    ib = Image.open(b).convert("RGB")
    assert ia.size == ib.size, f"size mismatch {ia.size} vs {ib.size}"
    diff = ImageChops.difference(ia, ib).convert("L").point(lambda v: 255 if v else 0)
    w, h = ia.size
    rows, cols = [0.0] * bands, [0.0] * bands
    px = diff.load()
    for y in range(h):
        band = min(int(y * bands / h), bands - 1)
        for x in range(w):
            if px[x, y]:
                rows[band] += 1
                cols[min(int(x * bands / w), bands - 1)] += 1
    for i, v in enumerate(rows):
        rows[i] = v / (w * h / bands) * 100
    for i, v in enumerate(cols):
        cols[i] = v / (w * h / bands) * 100
    print(f"{a.name} vs {b.name} ({w}x{h})")
    print("row bands  (top->bottom): " + " ".join(f"{v:5.1f}" for v in rows))
    print("col bands  (left->right): " + " ".join(f"{v:5.1f}" for v in cols))


if __name__ == "__main__":
    main()
