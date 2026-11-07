"""Text coverage on PSP: PPSSPP has no Lua, so the log is a BU_PRINTLOG run on the marker build, whose strings carry their id.
usage: cover.py LOGDIR [--kinds] -> LOGDIR/log.txt (TEXT lines for textcover.py), build/strings.tsv, and what wasn't reached,
counted per script file. Then: textcover.py LOGDIR build/strings.tsv --waive docs/text_unshown.tsv
Limit: a marked string counts once the printer gets it; inline names (codes 03, 04) and strings drawn by the game's own
layout routines never pass the printer's entry, so they read as not reached."""
import collections
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAG = re.compile(r"\[([EFB]\d+(?:\.\d+)?)\]")

log = Path(sys.argv[1])
ids = dict(line.split() for line in (ROOT / "work/marker_ids.tsv").read_text(encoding="utf-8").splitlines())
index = {tag: i for i, tag in enumerate(ids)}
seen = {m for p in log.glob("*.tsv") for m in TAG.findall(p.read_text(encoding="utf-8", errors="replace")) if m in ids}
(log / "log.txt").write_text("".join(f"TEXT {index[t]:x}\n" for t in sorted(seen, key=index.get)), encoding="utf-8")
(ROOT / "build/strings.tsv").write_text("".join(f"{ids[t]}\t{index[t]:x}\n" for t in ids), encoding="utf-8", newline="\n")
left = collections.Counter(ids[t].rsplit("_", 1)[0] for t in ids if t not in seen)
print(f"{len(seen)} of {len(ids)} strings reached")
for name, n in left.most_common():
    print(f"{n}\t{name}")
