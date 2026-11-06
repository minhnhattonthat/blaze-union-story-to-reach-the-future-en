"""Find Japanese text (Shift-JIS) across the EBOOT, unpacked CPK files and FCT children.
usage: grepjp.py TEXT [TEXT...]  -> file, offset, surrounding text"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
files = [ROOT / "work/exe/code.bin"] + sorted((ROOT / "work/cpk").glob("*.bin")) + sorted((ROOT / "work/fct").glob("*/*.bin"))
blobs = [(p, p.read_bytes()) for p in files]
for text in sys.argv[1:]:
    n = text.encode("cp932")
    for p, d in blobs:
        for m in re.finditer(re.escape(n), d):
            s = d[max(0, m.start() - 30):m.start() + 50]
            print(f"{p.parent.name}/{p.name} {m.start():#x}: {s.decode('cp932', 'replace')!r}")
