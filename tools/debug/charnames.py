"""The units' name ids: the character table (0x60-odd bytes of live data, read by 0xE29B0; +0x22 is the name id 0xE3444 prints). Writes data/unit_names.tsv:
name id, record id of the name, its Japanese. Only these names can reach union_name and unit_name; the rest of the name table is speakers and places.
usage: charnames.py [--iso ISO]"""
import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scenes
import warp

ROOT = warp.ROOT
TABLE, STRIDE = warp.SEG1 + 0x89BE8, 60
NAMES, NAME_STRIDE = 0x2ADE7C, 12
ap = argparse.ArgumentParser()
ap.add_argument("--iso", default=warp.ISO)
a = ap.parse_args()
slots = {}
for f in (ROOT / "script").glob("eboot_*.json"):
    for r in json.loads(f.read_text(encoding="utf-8")):
        for s in r["slots"]:
            if "word" in s:
                slots[s["word"]] = r
run = warp.psp.Run(warp.psp.find_emu(None), a.iso, str(ROOT / "work/qa/charnames"))
try:
    for fn, *args in scenes.SCENES["field"][0]:
        fn(run, *args)
    d = run.ws.mem(TABLE, STRIDE * 1024)
finally:
    run.close()
ids = {}
for i in range(1024):
    nid = struct.unpack_from("<H", d, i * STRIDE + 0x22)[0]
    r = slots.get(NAMES + nid * NAME_STRIDE)
    if r:
        ids.setdefault(nid, r)
rows = [f"{n}\t{r['id']}\t{r['jp']}\n" for n, r in sorted(ids.items())]
(ROOT / "data/unit_names.tsv").write_text("".join(rows), encoding="utf-8", newline="\n")
print(len(rows), "unit names")
