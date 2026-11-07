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
if len(sys.argv) < 2:  # no survey: keep the windows it saw, only redo the blocks below
    by_name = {w["name"]: w for w in windows}
    for line in (ROOT / "data/box_ids.tsv").read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if p[4] == "seen":
            out[p[0]] = by_name[p[1]]
for f in Path(sys.argv[1]).glob("*.tsv") if len(sys.argv) > 1 else ():
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
BLOCKS = ((0x1E0A30, 0x228000, "battle_cry"), (0x228B10, 0x22DC40, "battle_tip"), (0x22F254, 0x22F330, "tutorial_title"), (0x22F818, 0x230390, "object_text"),
          (0x231890, 0x234AA0, "book_item_text"), (0x234AB8, 0x235760, "book_name"), (0x235770, 0x235BD0, "item_name_equip"), (0x280000, 0x288000, "map_ticker"))
BOOK_PAGES = (0x25FB74, 0x263850)  # a title then its text, by turns: only the text has a break
for f in (ROOT / "script").glob("*.json"):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r["id"] in out or r["kind"] not in ("msg", "unref", "inline", "bare"):
            continue
        if not r["id"].startswith("eboot_"):
            out[r["id"]] = named["speaker" if r["kind"] == "inline" else "dialogue"]  # scripts print through these two
        for lo, hi, name in BLOCKS:
            if lo <= r["ptr"] < hi:
                out[r["id"]] = named[name]
        if BOOK_PAGES[0] <= r["ptr"] < BOOK_PAGES[1]:
            townsfolk = 0x261D0C <= r["ptr"] < 0x261F20 and len(r["jp"]) >= 7  # one-line texts: titles here are up to 6 characters
            out[r["id"]] = named["book_text" if "{n}" in r["jp"] or townsfolk else "book_list"]
rows = sorted(f"{i}\t{w['name']}\t{w['px']}\t{w['rows']}\t{'seen' if i in seen else 'inferred'}\n" for i, w in out.items())
(ROOT / "data/box_ids.tsv").write_text("".join(rows), encoding="utf-8", newline="\n")
print(f"mapped {len(out)} of {len(ids)} records")
for ra, t in sorted(missing.items()):
    print(f"no window for caller {ra:#x}, e.g. {t}")
