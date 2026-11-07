"""How the script already renders a Japanese term: first records whose jp holds it, with their en.
usage: term.py TERM.. [-n N]   (N hits per term, default 2)"""
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
args = sys.argv[1:]
n = 2
if "-n" in args:
    i = args.index("-n")
    n = int(args[i + 1])
    del args[i:i + 2]
hits = {t: 0 for t in args}
for f in sorted(glob.glob(str(ROOT / "script/*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    recs = d if isinstance(d, list) else d.get("records", [])
    for r in recs:
        jp, en = r.get("jp", ""), r.get("en", "")
        for t in hits:
            if t in jp and en and hits[t] < n:
                hits[t] += 1
                print(f"{t}\t{jp[:50]!r}\t{en[:140]!r}")
for t, k in hits.items():
    if not k:
        print(f"{t}\t(no translated record)")
