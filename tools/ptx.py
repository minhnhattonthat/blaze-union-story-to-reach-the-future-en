"""PTX@ texture decoder (Sting PSP). Layout (verified by rendering, see docs/re/graphics.md):
+0 'PTX@', +4 log2 tex w, +5 log2 tex h, +6 u16 stride, +8 u16 w, +a u16 h, +c u8 GU pixel format (4 T4, 5 T8), +d flags,
+e u8, +f bits, +10 u32 palette count, +14 u32 misc, +18 u32 palette offset, +1c u32 data offset. Palette RGBA8888.
usage: ptx.py FILE [OUT.png] [--swizzle]; library: parse(bytes, off=0) -> dict, decode(bytes, off=0) -> PIL.Image"""
import struct
import sys


def parse(d, off=0):
    assert d[off:off + 4] == b"PTX@", d[off:off + 4]
    lw, lh, stride, w, h, fmt, flags, b2, bits, npal, misc, poff, doff = struct.unpack_from("<BBHHHBBBBIIII", d, off + 4)
    return dict(lw=lw, lh=lh, stride=stride, w=w, h=h, fmt=fmt, flags=flags, b2=b2, bits=bits, npal=npal, misc=misc,
                poff=poff, doff=doff, off=off)


def unswizzle(data, stride_bytes, rows):
    """PSP swizzle: 16-byte x 8-row blocks in row-major block order."""
    out = bytearray(stride_bytes * rows)
    src = 0
    for by in range(0, rows, 8):
        for bx in range(0, stride_bytes, 16):
            for y in range(8):
                if by + y < rows:
                    p = (by + y) * stride_bytes + bx
                    out[p:p + 16] = data[src:src + 16]
                src += 16
    return bytes(out)


def decode(d, off=0, swizzle=None):
    from PIL import Image
    h = parse(d, off)
    bpp = {4: 4, 5: 8}.get(h["fmt"])
    if bpp is None:
        raise ValueError(f"format {h['fmt']}")
    pal = struct.unpack_from(f"<{h['npal']}I", d, off + h["poff"])
    stride = h["stride"]
    sb = stride * bpp // 8
    # shortcut: the swizzle flag bit is not pinned down yet, callers can force it; default follows flags & 1
    sw = bool(h["flags"] & 1) if swizzle is None else swizzle
    raw = d[off + h["doff"]:off + h["doff"] + sb * h["h"] + 16 * 8]
    if sw:
        # swizzle works on whole 8-row blocks, so pad rows up
        rows = (h["h"] + 7) & ~7
        raw = unswizzle(raw.ljust(sb * rows, b"\0"), max(sb, 16), rows)
        sb = max(sb, 16)
    img = Image.new("RGBA", (h["w"], h["h"]))
    px = img.load()
    for y in range(h["h"]):
        row = raw[y * sb:(y + 1) * sb]
        for x in range(h["w"]):
            if bpp == 8:
                i = row[x] if x < len(row) else 0
            else:
                b = row[x >> 1] if (x >> 1) < len(row) else 0
                i = (b >> 4) if x & 1 else (b & 15)
            c = pal[i] if i < len(pal) else 0
            px[x, y] = (c & 255, (c >> 8) & 255, (c >> 16) & 255, (c >> 24) & 255)
    return img


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    print(parse(d))
    if len(sys.argv) > 2 and not sys.argv[2].startswith("--"):
        decode(d, swizzle=("--swizzle" in sys.argv) or None).save(sys.argv[2])
