"""Bisect the marker build: hooks and fonts stay, only the strings a filter accepts get markers.
usage: variant.py PREFIX[,PREFIX..] OUT.iso   string file names starting with a PREFIX are marked (event_, fct3_15_, eboot, ..).
Then: scenes.py NAME --iso OUT.iso. ~name means every file except those starting with name."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build
import insert
import marker

want, out = sys.argv[1].split(","), sys.argv[2]
inv = want[0].startswith("~")
want = [w.lstrip("~") for w in want]
m = marker.Marker()


def text(r, name):
    hit = any(name.startswith(w) for w in want)
    return m(r, name) if hit != inv else None


text.fit = m.fit
repl, eboot, n = insert.build(text)
print("marked", n)
build.build(out, repl=repl, keep_same=False, eboot=eboot)
