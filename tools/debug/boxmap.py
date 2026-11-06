"""Width gate: from a BU_PRINTLOG survey of the marker build, write data/box_ids.tsv: record id, window name (data/windows.json), px, rows.
A string seen in several windows takes the smallest. Prints callers missing from windows.json and how many records are mapped.
usage: boxmap.py LOGDIR"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
windows = json.loads((ROOT / "data/windows.json").read_text(encoding="utf-8"))
by_caller = {int(c, 0): w for w in windows for c in w["callers"]}
ids = dict(l.split() for l in (ROOT / "work/marker_ids.tsv").read_text(encoding="utf-8").splitlines())
out, missing = {}, {}
for f in Path(sys.argv[1]).glob("*.tsv"):
    for line in f.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        ra = int(p[0], 0)
        tags = [t for t in re.findall(r"\[([EFB][0-9.]+)\]", p[12]) if t in ids]
        w = by_caller.get(ra)
        if w is None:
            if tags:
                missing.setdefault(ra, tags[0])
            continue
        for t in tags:
            if w["px"] and (ids[t] not in out or w["px"] < out[ids[t]]["px"]):
                out[ids[t]] = w
named = {w["name"]: w for w in windows}
seen = set(out)
# Unseen strings by what they sit next to, read off script/eboot_*.json: one screen's sample stands for its block. The fifth column says so
BLOCKS = ((0x1E4000, 0x228000, "battle_cry"), (0x280000, 0x288000, "map_ticker"))
for f in (ROOT / "script").glob("*.json"):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r["id"] in out or r["kind"] not in ("msg", "unref", "inline", "bare"):
            continue
        if not r["id"].startswith("eboot_"):
            out[r["id"]] = named["speaker" if r["kind"] == "inline" else "dialogue"]  # scripts print through these two
        for lo, hi, name in BLOCKS:
            if lo <= r["ptr"] < hi:
                out[r["id"]] = named[name]
rows = sorted(f"{i}\t{w['name']}\t{w['px']}\t{w['rows']}\t{'seen' if i in seen else 'inferred'}\n" for i, w in out.items())
(ROOT / "data/box_ids.tsv").write_text("".join(rows), encoding="utf-8", newline="\n")
print(f"mapped {len(out)} of {len(ids)} records")
for ra, t in sorted(missing.items()):
    print(f"no window for caller {ra:#x}, e.g. {t}")
