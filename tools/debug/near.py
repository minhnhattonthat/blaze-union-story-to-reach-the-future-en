"""Script records around exact Japanese strings, to reuse their English for sprite text.
usage: near.py JP.. [-n N]   (N records after each hit, default 45)"""
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
args = sys.argv[1:]
n = 45
if "-n" in args:
    i = args.index("-n")
    n = int(args[i + 1])
    del args[i:i + 2]
for f in sorted(glob.glob(str(ROOT / "script/*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    recs = d if isinstance(d, list) else d.get("records", [])
    for i, r in enumerate(recs):
        if r.get("jp", "").replace("{n}", "") in args:
            print(f"== {Path(f).name} {i}")
            for y in recs[i:i + n]:
                print(y.get("jp", "").replace("{n}", ""), "|", y.get("en", "").replace("{n}", " / "), sep="\t")
