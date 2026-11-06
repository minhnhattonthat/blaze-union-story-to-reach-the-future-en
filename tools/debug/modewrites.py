"""Who sets the top-level mode: every store to seg1 0x808B4 in work/exe/dis.txt with the value loaded just before it.
usage: modewrites.py [MODE..]  (needs tools/disall.py output)"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
lines = (ROOT / "work/exe/dis.txt").read_text().splitlines()
want = {int(x, 0) for x in sys.argv[1:]}
for i, line in enumerate(lines):
    m = re.search(r"sw \$(\w+), 0x8b4\(", line)
    if not m:
        continue
    val = "?"
    for back in lines[max(0, i - 8):i + 2][::-1]:
        v = re.search(rf"(?:ori|addiu) \${m.group(1)}, \$zero, (-?\w+)", back)
        if v:
            val = int(v.group(1), 0)
            break
    if not want or val in want:
        print(val, line.split()[0])
