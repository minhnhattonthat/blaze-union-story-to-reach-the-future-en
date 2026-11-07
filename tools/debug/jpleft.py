"""Leftover Japanese in the built EBOOT that a pointer still reaches: writes work/qa/jp_slots.txt (every text slot, resolved in the built EBOOT) and runs the skill's jp_left.py.
usage: jpleft.py [ISO]. Exit 1 if any run is left outside script/keep_jp.txt and the `debug` records. The event scripts are checked by the build's own text."""
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build
from skill import SKILL

iso = sys.argv[1] if len(sys.argv) > 1 else build.OUT
eb = build.extract(iso, build.EBOOT)
out = ROOT / "work/qa/jp_eboot.bin"
out.write_bytes(eb)
ph = struct.unpack_from("<I", eb, 0x1C)[0]
segs = [struct.unpack_from("<8I", eb, ph + 32 * i) for i in range(struct.unpack_from("<H", eb, 0x2C)[0])]  # type, offset, vaddr, paddr, filesz, memsz, flags, align


def file_of(va):
    for s in segs:
        if s[0] == 1 and s[2] <= va < s[2] + s[4]:
            return s[1] + va - s[2]
    return None


GROW = segs[0][1]  # segment 0's file offset: a slot's vaddr + this
skip = {line.split("\t")[0] for line in (ROOT / "script/keep_jp.txt").read_text(encoding="utf-8").splitlines()}
lines = []
for f in sorted((ROOT / "script").glob("eboot_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r["id"] in skip or r["kind"] in ("data", "debug"):  # debug: printf logs, no table points at them (tests/test_extract.py)
            continue
        for s in r["slots"]:
            if "word" in s:
                at = s["word"] + GROW
                va = struct.unpack_from("<I", eb, at)[0]
            else:
                at = s["hi"] + GROW
                hi, lo = (struct.unpack_from("<H", eb, x + GROW)[0] for x in (s["hi"], s["lo"]))
                va = (hi << 16) + (lo - 0x10000 if lo & 0x8000 else lo)
            t = file_of(va)
            if t is not None:
                lines.append(f"{at:X} {t:X}\n")
slots = ROOT / "work/qa/jp_slots.txt"
slots.write_text("".join(lines), newline="\n")
print(len(lines), "slots")
sys.exit(subprocess.call([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts/jp_left.py"), str(out), "--sjis", "--slots", str(slots), "--limit", "60"]))
