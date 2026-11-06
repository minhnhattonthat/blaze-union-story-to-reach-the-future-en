"""Walk the call graph up from code addresses to the top-level mode handlers (table at vaddr 0x270810).
usage: callup.py ADDR.. (hex vaddr; needs work/exe/dis.txt from tools/disall.py)
Function starts are approximated: an `addiu $sp, $sp, -N` not preceded by a stack use in the same function; jal only, so
calls through pointers break the chain (shown as "top")."""
import bisect
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
lines = (ROOT / "work/exe/dis.txt").read_text().splitlines()
code = (ROOT / "work/exe/code.bin").read_bytes()
MODES = {struct.unpack_from("<I", code, 0x270810 + 4 * i)[0]: i for i in range(43)}
starts, calls = [], {}
for l in lines:
    p = l.split(" ", 2)
    a = int(p[0], 16)
    if p[1] == "addiu" and p[2].startswith("$sp, $sp, -"):
        starts.append(a)
starts += list(MODES)
starts = sorted(set(starts))


def func(a):
    return starts[bisect.bisect_right(starts, a) - 1]


for l in lines:
    m = re.match(r"(\w+) j(?:al)? (0x[0-9a-f]+)", l)
    if m:
        calls.setdefault(int(m.group(2), 16), []).append(int(m.group(1), 16))


def up(a, seen, depth, out, path):
    f = func(a)
    path = path + [f]
    if f in MODES:
        out.append(path + [f"mode {MODES[f]}"])
        return
    if f in seen or depth > 12:
        return
    seen.add(f)
    callers = calls.get(f, [])
    if not callers:
        out.append(path + ["top"])
    for c in callers:
        up(c, seen, depth + 1, out, path)


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        out = []
        up(int(arg, 16), set(), 0, out, [])
        print(arg)
        for p in out[:6]:
            print("  ", " < ".join(x if isinstance(x, str) else hex(x) for x in p))
