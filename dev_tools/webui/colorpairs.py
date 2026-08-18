"""Report the most common (old, new) color pairs among differing pixels.

Usage: python dev_tools/webui/colorpairs.py <img-a> <img-b> [limit]
"""

import sys
from collections import Counter
from pathlib import Path

from PIL import Image


def main():
    a, b = Path(sys.argv[1]), Path(sys.argv[2])
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    ia = Image.open(a).convert("RGB")
    ib = Image.open(b).convert("RGB")
    assert ia.size == ib.size, "size mismatch"
    counter = Counter()
    pa, pb = ia.load(), ib.load()
    w, h = ia.size
    for y in range(h):
        for x in range(w):
            if pa[x, y] != pb[x, y]:
                counter[(pa[x, y], pb[x, y])] += 1
    total = sum(counter.values())
    print(f"{total} differing pixels ({total / (w * h) * 100:.2f}%)")
    for (old, new), count in counter.most_common(limit):
        print(f"{count / total * 100:6.2f}%  old {old} -> new {new}")


if __name__ == "__main__":
    main()
