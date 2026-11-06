"""Stress build for the repacker: every compressed file stored raw, script 2149 padded past 64K, archive moved to the end
of the image. If this boots and plays, later edited files can be stored raw and can grow. Reads the work/cpk unpack.
usage: stress_build.py [OUT]   then warp.py / scenes.py --iso OUT"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build

repl = {}
for line in (ROOT / "work/cpk/index.tsv").read_text(encoding="utf-8").splitlines():
    fid, _, _, _, comp, ext, _ = line.split("\t")
    if comp == "1":
        repl[int(fid)] = (ROOT / f"work/cpk/{int(fid):05d}.{ext}").read_bytes()
repl[2149] += bytes(70000 - len(repl[2149]))  # zeros past the script's end; only the size changes
out = build.build(sys.argv[1] if len(sys.argv) > 1 else ROOT / "work/qa/stress.iso", repl=repl, keep_same=False)
print(out, out.stat().st_size)
