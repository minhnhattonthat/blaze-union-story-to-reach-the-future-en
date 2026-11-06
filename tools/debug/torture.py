"""Width gate tools: a marker build with chosen strings overridden, so a box can be filled to a known pixel width.
usage: torture.py OUT.iso ID=TEXT [ID=TEXT ..]    ID = a record id (eboot_25C9A8, event_2150_00012) or a marker tag (E2150.0).
TEXT uses {n}. Special: ID=@PX fills the first line to PX pixels in the 20 px font and marks the end with '|'."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build
import insert
import marker
import vwf

TORTURE = "".join(chr(c) for c in range(0x21, 0x7F)) + "  double  spaces"


def fill(px, font=1):
    """Text exactly px wide (to the far side of its last glyph's advance) in the font, ending in '|'."""
    w = vwf.widths()[font]
    s, x = "", 0
    bar = w[ord("|")]
    pat = "The quick brown fox jumps over the lazy dog "
    while True:
        c = pat[len(s) % len(pat)]
        if x + w[ord(c)] + bar > px:
            break
        s += c
        x += w[ord(c)]
    return s + "|", x + bar


if __name__ == "__main__":
    out = sys.argv[1]
    over = dict(a.split("=", 1) for a in sys.argv[2:])
    m = marker.Marker()
    for k, v in over.items():
        if v.startswith("@"):
            over[k] = fill(int(v[1:]))[0]
        elif v == "TORTURE":
            over[k] = TORTURE

    def text(r, name):
        s = m(r, name)
        if s is None:
            return None
        return over.get(r["id"], over.get(m.tag, s))

    text.fit = m.fit
    repl, eboot, n = insert.build(text)
    build.build(out, repl=repl, keep_same=False, eboot=eboot)
