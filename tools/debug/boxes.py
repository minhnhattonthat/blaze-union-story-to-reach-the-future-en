"""Box survey: group a BU_PRINTLOG run by caller and window. usage: boxes.py LOGDIR ISO
One row per variant: caller, window x y, cols x rows, spacing, font, its px width (cols * (cell + sp)), strings seen, sample tags."""
import collections
import glob
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import iso9660

BASE = 0x08804000
CELL = {0: 8, 1: 20, 2: 18, 3: 24, 4: 12}


def eboot_strings(iso):
    with open(iso, "rb") as f:
        _, lba, size, _ = next(e for e in iso9660.listing(f) if e[0] == "/PSP_GAME/SYSDIR/EBOOT.BIN")
        f.seek(lba * 2048)
        elf = f.read(size)
    ph = struct.unpack_from("<8I", elf, 0x34 + 2 * 32)
    return elf[ph[1]:ph[1] + ph[4]], ph[2]


blob, seg = eboot_strings(sys.argv[2])
groups = collections.defaultdict(lambda: [0, [], set()])
for f in glob.glob(sys.argv[1] + "/*.tsv"):
    for line in open(f, encoding="utf-8"):
        ra, x, y, cols, rows, spx, spy, col, row, font, text, pc = line.rstrip("\n").split("\t")[:12]
        font = int(font, 0) & 0xFFFF
        font = font - 16 if font >= 16 else font
        v = int(text, 16) - BASE
        tag = "script"
        if seg <= v < seg + len(blob):
            s = blob[v - seg:v - seg + 40]
            m = re.search(rb"\[(B\d+)\]", s)
            tag = m[1].decode() if m else "?"
        g = groups[ra, int(cols), int(rows), font, int(spx), int(spy)]
        g[0] += 1
        g[2].add((int(x), int(y)))
        if tag not in g[1] and len(g[1]) < 3:
            g[1].append(tag)
print("caller  cols rows font sp  px  n  at  tags")
for (ra, cols, rows, font, spx, spy), (n, tags, at) in sorted(groups.items(), key=lambda kv: -kv[1][0]):
    px = cols * (CELL.get(font, 0) + spx)
    print(ra, cols, rows, font, f"{spx},{spy}", px, n, sorted(at)[:2], " ".join(tags))
