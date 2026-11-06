"""PTG@ sprite group: a sprite cut into rects and packed into the PTX slices that follow it. See docs/re/graphics.md.
+4 u32 cell table offset (0x20), +8 u32 first PTX offset, +c u32 second PTX offset (0 = none), all from the PTG start,
+10 u16 w, +12 u16 h, +14 u16 cells in slice 0, +16 u16 cells in slice 1.
Cell (20 bytes): u16 sx0, sy0, dx0, dy0, zero, sx1, sy1, dx1, dy1, pad. Source rect in its slice, destination in the sprite.
usage: ptg.py FILE OFFSET OUT.png; library: parse(d, off) -> dict, render(d, off) -> PIL.Image"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ptx import decode, palette


def parse(d, off=0):
    assert d[off:off + 4] == b"PTG@", d[off:off + 4]
    table, p0, p1, w, h, n0, n1 = struct.unpack_from("<IIIHHHH", d, off + 4)
    cells = [struct.unpack_from("<10H", d, off + table + 20 * i) for i in range(n0 + n1)]
    return dict(off=off, table=table, slices=[off + p for p in (p0, p1) if p], w=w, h=h, n0=n0, n1=n1, cells=cells)


def render(d, off=0, pal=None):
    from PIL import Image
    g = parse(d, off)
    src = []
    for s in g["slices"]:
        pal = palette(d, s) or pal  # a second slice has no palette of its own
        src.append(decode(d, s, pal=pal))
    # some cells reach past the declared size, so the canvas follows the cells
    w = max([g["w"]] + [c[7] for c in g["cells"]])
    h = max([g["h"]] + [c[8] for c in g["cells"]])
    img = Image.new("RGBA", (w, h))
    for i, (sx0, sy0, dx0, dy0, _, sx1, sy1, dx1, dy1, _) in enumerate(g["cells"]):
        img.paste(src[i >= g["n0"]].crop((sx0, sy0, sx1, sy1)), (dx0, dy0))
    return img


if __name__ == "__main__":
    data = Path(sys.argv[1]).read_bytes()
    render(data, int(sys.argv[2], 0)).save(sys.argv[3])
