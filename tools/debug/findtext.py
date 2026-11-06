"""Where does a string live? Searches script/*.json, then the EBOOT and every Data.cpk file raw. usage: findtext.py TEXT [TEXT..]
A hit in neither means it is drawn as a graphic (docs/re/graphics.md)."""
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
recs = [(r["id"], r["kind"], r["jp"]) for f in glob.glob(str(ROOT / "script/*.json")) for r in json.load(open(f, encoding="utf-8"))]
blobs = [("eboot", (ROOT / "work/exe/code.bin").read_bytes())]
blobs += [(p.name, p.read_bytes()) for p in sorted((ROOT / "work/cpk").iterdir()) if p.is_file() and p.suffix != ".tsv" and p.stat().st_size < 8_000_000]
for t in sys.argv[1:]:
    hits = [f"{i} {k}" for i, k, j in recs if t in j][:4]
    raw = [f"{n}@{d.find(t.encode('cp932')):#x}" for n, d in blobs if t.encode("cp932") in d][:4]
    print(t, "| records:", hits or "none", "| raw:", raw or "none")
