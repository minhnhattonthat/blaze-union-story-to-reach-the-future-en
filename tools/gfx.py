"""Write English sprites back: PTX@ encoder (same size, same palette) and a PTG@ repacker. See docs/re/graphics.md.
A PTG's slices are one stream of 8-row columns: each 8-row band of the sprite, trimmed to its ink, is laid in the
stream left to right, slice row after slice row, a cell per run (split where a slice row ends). repack() redoes that for
a new image within the old slices and cell count, so the file keeps its size and every offset.
Library: indices(d, off) / put_indices(d, off, idx) for one PTX; quantize(img, pal); write_ptx(d, off, img);
repack(d, goff, img); sprites(d) -> {first slice offset: ('ptg', goff) | ('ptx', off)}; copies(blob) -> [(fid, off)]."""
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ptg
import ptx

CPK = Path(__file__).resolve().parent.parent / "work/cpk"


def _geom(h):
    bpp = 8 if h["fmt"] == 5 else 4
    sb = h["stride"] * bpp // 8
    sw = bool(h["flags"] & 1)
    rows = (h["h"] + 7) & ~7 if sw else h["h"]
    return bpp, sb, sw, rows


def indices(d, off):
    """-> list of rows of palette indices, h rows of w."""
    h = ptx.parse(d, off)
    bpp, sb, sw, rows = _geom(h)
    raw = d[off + h["doff"]:off + h["doff"] + sb * rows]
    if sw:
        raw = ptx.unswizzle(raw.ljust(max(sb, 16) * rows, b"\0"), max(sb, 16), rows)
        sb = max(sb, 16)
    out = []
    for y in range(h["h"]):
        row = raw[y * sb:(y + 1) * sb]
        if bpp == 8:
            out.append(list(row[:h["w"]]))
        else:
            out.append([(row[x >> 1] >> (4 * (x & 1))) & 15 for x in range(h["w"])])
    return out


def swizzle(data, stride_bytes, rows):
    out = bytearray()
    for by in range(0, rows, 8):
        for bx in range(0, stride_bytes, 16):
            for y in range(8):
                p = (by + y) * stride_bytes + bx
                out += data[p:p + 16]
    return bytes(out)


def put_indices(d, off, idx):
    """Write rows of indices into the PTX at off (bytearray d). Padding columns and rows keep their old bytes."""
    h = ptx.parse(d, off)
    bpp, sb, sw, rows = _geom(h)
    start = off + h["doff"]
    if sw and sb < 16:
        raise ValueError("stride under one swizzle block")  # none in this game; decode pads, encode would not
    raw = bytearray(d[start:start + sb * rows])
    if sw:
        raw = bytearray(ptx.unswizzle(bytes(raw), sb, rows))
    for y, r in enumerate(idx):
        if bpp == 8:
            raw[y * sb:y * sb + len(r)] = bytes(r)
        else:
            for x, i in enumerate(r):
                p = y * sb + (x >> 1)
                raw[p] = (raw[p] & 0xF0) | i if x & 1 == 0 else (raw[p] & 0x0F) | (i << 4)
    d[start:start + sb * rows] = swizzle(bytes(raw), sb, rows) if sw else raw


def rgba(c):
    return c & 255, (c >> 8) & 255, (c >> 16) & 255, c >> 24


def quantize(img, pal):
    """RGBA image -> rows of nearest palette indices (RGBA distance; alpha 0 -> the clearest entry)."""
    cols = [rgba(c) for c in pal]
    clear = min(range(len(cols)), key=lambda i: cols[i][3])
    cache = {}
    px = img.convert("RGBA").load()
    out = []
    for y in range(img.height):
        row = []
        for x in range(img.width):
            p = px[x, y]
            if p[3] == 0:
                row.append(clear)
                continue
            i = cache.get(p)
            if i is None:
                i = cache[p] = min(range(len(cols)), key=lambda j: sum((a - b) ** 2 for a, b in zip(p, cols[j])))
            row.append(i)
        out.append(row)
    return out


def group_palette(d, goff):
    """Palette of a group's first slice, or of the nearest PTX before it that has one (poff 0 shares)."""
    s = ptg.parse(d, goff)["slices"][0]
    pal = ptx.palette(d, s)
    o = s
    while pal is None:
        o = d.rfind(b"PTX@", 0, o)
        if o < 0:
            raise ValueError("no palette before group")
        pal = ptx.palette(d, o)
    return pal


def write_ptx(d, off, img, pal=None):
    h = ptx.parse(d, off)
    assert img.size == (h["w"], h["h"]), (img.size, h["w"], h["h"])
    put_indices(d, off, quantize(img, ptx.palette(d, off) or pal))


def _runs(idx, W, H, ink, gap_max):
    """(y, x0, x1) per 8-row band, trimmed to ink; a blank gap of gap_max+ columns splits a band."""
    runs = []
    for y in range(0, H, 8):
        band = [idx[r] for r in range(y, min(y + 8, H))]
        on = [any(ink(b[x]) for b in band) for x in range(W)]
        x = 0
        while x < W:
            if not on[x]:
                x += 1
                continue
            x0, gap, x1 = x, 0, x
            while x < W and gap < gap_max:
                if on[x]:
                    x1, gap = x + 1, 0
                else:
                    gap += 1
                x += 1
            runs.append((y, x0, x1))
    return runs


def repack(d, goff, img, pal=None):
    """Lay img (RGBA, the size ptg.render gives) into the group's slices. Wide gaps are kept first (fewer cells), then
    cut tighter until the ink fits the stream; ValueError if it never fits the columns and cell count the group has.
    Unused cells repeat the last one (drawn twice, same pixels)."""
    pal = pal or group_palette(d, goff)
    cols = [rgba(c) for c in pal]
    idx = quantize(img, pal)
    err = None
    for gap in (64, 24, 8, 3, 1):
        try:
            return _lay(d, goff, idx, img.size, cols, gap)
        except ValueError as e:
            err = e
    raise err


def _lay(d, goff, idx, size, cols, gap):
    g = ptg.parse(d, goff)
    clear = min(range(len(cols)), key=lambda i: cols[i][3])
    W, H = size
    runs = _runs(idx, W, H, lambda i: cols[i][3] > 0, gap)
    heads = [ptx.parse(d, s) for s in g["slices"]]
    slots = [(si, row) for si, h in enumerate(heads) for row in range(0, h["h"], 8)]
    bufs = [[[clear] * h["w"] for _ in range(h["h"])] for h in heads]
    cells = [[] for _ in heads]
    k, cx = 0, 0
    for y, x0, x1 in runs:
        while x0 < x1:
            if k >= len(slots):
                raise ValueError(f"group {goff:#x}: ink needs more than the {len(slots)} slice rows")
            si, sy = slots[k]
            wmax = heads[si]["w"]
            n = min(x1 - x0, wmax - cx)
            for r in range(8):
                if y + r < H and sy + r < heads[si]["h"]:
                    bufs[si][sy + r][cx:cx + n] = idx[y + r][x0:x0 + n]
            cells[si].append((cx, sy, x0, y, 0, cx + n, sy + 8, x0 + n, y + 8, 0))
            x0 += n
            cx += n
            if cx >= wmax:
                k, cx = k + 1, 0
    total = g["n0"] + g["n1"]
    used = sum(map(len, cells))
    if used > total:
        raise ValueError(f"group {goff:#x}: {used} cells, has {total}")
    if not used:
        cells[0].append((0, 0, 0, 0, 0, 1, 8, 1, 8, 0))
        used = 1
    last = len(heads) - 1 if len(cells) > 1 and cells[-1] else 0
    cells[last] += [cells[last][-1]] * (total - used)
    for si, s in enumerate(g["slices"]):
        put_indices(d, s, bufs[si])
    struct.pack_into("<HH", d, goff + 0x14, len(cells[0]), len(cells[1]) if len(cells) > 1 else 0)
    for i, c in enumerate(cells[0] + (cells[1] if len(cells) > 1 else [])):
        struct.pack_into("<10H", d, goff + g["table"] + 20 * i, *c)


def ptx_size(d, off):
    h = ptx.parse(d, off)
    bpp, sb, sw, rows = _geom(h)
    return h["doff"] + sb * rows


def snapped(img, pal):
    """img as the palette will show it (what the game draws after quantize)."""
    from PIL import Image
    cols = [rgba(c) for c in pal]
    out = Image.new("RGBA", img.size)
    out.putdata([cols[i] for r in quantize(img, pal) for i in r])
    return out


def span(d, goff):
    """Bytes a group owns: header to the end of its last slice."""
    g = ptg.parse(d, goff)
    h = ptx.parse(d, g["slices"][-1])
    bpp, sb, sw, rows = _geom(h)
    return goff, g["slices"][-1] + h["doff"] + sb * rows


def sprites(d):
    """{first slice offset (the sweep's label): ('ptg', group offset) or ('ptx', offset)}"""
    out = {}
    owned = set()
    for m in re.finditer(b"PTG@", d):
        try:
            g = ptg.parse(d, m.start())
        except struct.error:
            continue
        if g["slices"] and all(d[s:s + 4] == b"PTX@" for s in g["slices"]):
            out[g["slices"][0]] = ("ptg", m.start())
            owned.update(g["slices"])
    for m in re.finditer(b"PTX@", d):
        if m.start() not in owned:
            out[m.start()] = ("ptx", m.start())
    return out


_files = {}


def copies(blob):
    """Every (file id, offset) in work/cpk holding these exact bytes."""
    if not _files:
        for p in sorted(CPK.glob("*.bin")):
            _files[int(p.stem)] = p.read_bytes()
    out = []
    for fid, d in _files.items():
        o = d.find(blob)
        while o >= 0:
            out.append((fid, o))
            o = d.find(blob, o + 1)
    return out
