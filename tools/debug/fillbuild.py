"""Width gate build: every string the box survey saw is filled to its window's px width, ending in '|'; script lines to DIALOGUE px.
Where the '|' lands against the frame in a shot is the measurement. usage: fillbuild.py LOGDIR MARKER_ISO OUT.iso [--scale F]"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools/debug"))
import build
import insert
import marker
import torture
import vwf

DIALOGUE = 288
log, iso, out = sys.argv[1:4]
sys.argv = [sys.argv[0], log, iso]
scale = 1.0
# tag -> (px, font) from the survey, smallest window wins
src = (ROOT / "tools/debug/boxes.py").read_text(encoding="utf-8")
ns = {"__name__": "boxes_lib", "__file__": str(ROOT / "tools/debug/boxes.py")}
exec(compile(src.split("print(\"caller")[0], "boxes", "exec"), ns)
blob, seg = ns["blob"], ns["seg"]
fills = {}
for f in Path(log).glob("*.tsv"):
    for line in open(f, encoding="utf-8"):
        ra, x, y, cols, rows, spx, spy, col, row, font, text, pc = line.rstrip("\n").split("\t")[:12]
        fid = int(font, 0) & 0xFFFF
        fid = fid - 16 if fid >= 16 else fid
        v = int(text, 16) - ns["BASE"]
        if not seg <= v < seg + len(blob) or fid not in vwf.FONTS:
            continue
        m = re.search(rb"\[(B\d+)\]", blob[v - seg:v - seg + 40])
        if m:
            px = (int(cols) - int(col)) * (ns["CELL"][fid] + int(spx))
            if int(ra, 0) == 0x120944:  # shortcut: item names also go through 【%s】 in a 40-byte stack buffer (0x120824), 35 bytes at most
                px = 150
            tag = m[1].decode()
            if tag not in fills or px < fills[tag][0]:
                fills[tag] = (px, fid)
print("filled", len(fills))
widths = vwf.widths()
m = marker.Marker()


def fill(px, font):
    w, s, x = widths[font], "", 0
    pat = "The quick brown fox jumps over the lazy dog "
    while x + w[ord(pat[len(s) % len(pat)])] + w[ord("|")] <= px:
        x += w[ord(pat[len(s) % len(pat)])]
        s += pat[len(s) % len(pat)]
    return s + "|"


def text(r, name):
    s = m(r, name)
    if s is None or r["kind"] in ("inline", "bare"):
        return s
    if name.startswith("event_"):  # keep leading voice code and the line count
        lines = r["jp"].split("{n}")
        head = "".join(a for a in marker.ATOM.findall(lines[0]) if a.startswith("{voice"))
        return head + "{n}".join(fill(DIALOGUE, 1) for _ in lines)
    if m.tag in fills:
        px, font = fills[m.tag]
        codes = "".join(a for a in marker.ATOM.findall(r["jp"]) if a != "{n}")
        return codes + "{n}".join(fill(px, font) for _ in r["jp"].split("{n}"))
    return s


text.fit = m.fit
repl, eboot, n = insert.build(text)
build.build(out, repl=repl, keep_same=False, eboot=eboot)
