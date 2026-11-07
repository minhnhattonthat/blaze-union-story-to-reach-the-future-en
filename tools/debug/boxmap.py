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
# By the pointer table that holds them (word address, stride, offset in the row), read off the code that prints them: tools/debug/softwin.py lists the tables
SLOT_TABLES = ((0x2ADE7C, 0x2AEA98, 0, 0, "speaker"), (0x278748, 0x2787D0, 0, 0, "battle_tip"), (0x279704, 0x279858, 0, 0, "mission_brief"),
               (0x279C8C, 0x279E78, 12, 0, "card_text_list"), (0x279C8C, 0x279E78, 12, 4, "card_power"),(0x279C8C, 0x279E78, 12, 8, "card_qualify"), (0x286638, 0x286654, 0, 0, "tutorial_title"),
               (0x286CF0, 0x286D08, 0, 0, "object_text"), (0x28A020, 0x28A044, 0, 0, "result_message"), (0x28A094, 0x28A130, 0, 0, "card_poem"),
               (0x28AED4, 0x28AF00, 0, 0, "not_drawn"), (0x2ACFBC, 0x2AD020, 0, 0, "memstick"), (0x236DE8, 0x236FBC, 0, 0, "memstick"),
               (0x2AD34C, 0x2AD38C, 0, 0, "memstick"), (0x2B5B30, 0x2B5B80, 0, 0, "unit_intro"), (0x2B604C, 0x2B6480, 0, 0, "dialogue"),
               (0x2B6604, 0x2B6668, 0, 0, "book_text"), (0x2B8758, 0x2B87C4, 0, 0, "lose_condition"), (0x2B8810, 0x2B8B7C, 0, 0, "win_condition"))
BY_PTR = ((0x1E07B8, 0x1E0830, "morale_message"), (0x22EC4C, 0x22EFF0, "debug_menu"), (0x236690, 0x2369A0, "debug_menu"),
          (0x237058, 0x2370F1, "not_drawn"), (0x258D40, 0x258D6A, "not_drawn"))  # code slots only; not_drawn here: save details the system dialog shows, kind `debug`
sys.path.insert(0, str(ROOT / "tools/debug"))
import defeat_parts

code = (ROOT / "work/exe/code.bin").read_bytes()
news, game_over, _ = defeat_parts.ids(code)
for f in (ROOT / "script").glob("*.json"):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r["id"] in seen or not r["id"].startswith("eboot_"):
            continue
        hits = [named[n] for s in r["slots"] if "word" in s for lo, hi, stride, off, n in SLOT_TABLES
                if lo <= s["word"] < hi and (not stride or (s["word"] - lo) % stride == off)]
        hits += [named[n] for lo, hi, n in BY_PTR if lo <= r["ptr"] < hi]
        hits += [named["battle_news"]] * (r["id"] in news) + [named["game_over_text"]] * (r["id"] in game_over)
        if hits:
            out[r["id"]] = min(hits, key=lambda w: w["px"])
rows = sorted(f"{i}\t{w['name']}\t{w['px']}\t{w['rows']}\t{'seen' if i in seen else 'inferred'}\n" for i, w in out.items())
(ROOT / "data/box_ids.tsv").write_text("".join(rows), encoding="utf-8", newline="\n")
print(f"mapped {len(out)} of {len(ids)} records")
for ra, t in sorted(missing.items()):
    print(f"no window for caller {ra:#x}, e.g. {t}")
