"""Which rects of a texture does a screen draw? On a state showing the screen, overwrite the texture's pixels in RAM: once
opaque (each drawn rect shows as a blob), then with palette indexes coding y, then x (14 greys, so mod 14). Prints each
blob's screen box and its source rect. 4bpp swizzled PTX with a grey palette only (4@5e190, the difficulty prompt).
usage: texrects.py ISO STATE LABEL OUTDIR"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "tools"))
import ptx
import sprite
import warp

iso, state, label, out = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)
d, kind, off = sprite.load(label)
h = ptx.parse(d, off)
assert h["fmt"] == 4 and h["flags"] & 1, "4bpp swizzled only"
pal = ptx.palette(d, off)
grey = {i: pal[i] & 0xFF for i in range(16) if pal[i] >> 24 == 0xFF}
IDX = [i for i in sorted(grey, key=grey.get) if i][:14]
assert len(IDX) == 14, "needs 14 opaque palette entries"
sb, rows = h["stride"] // 2, (h["h"] + 7) & ~7
raw = d[off + h["doff"]:off + h["doff"] + sb * rows]


def swizzle(lin):
    o = bytearray()
    for by in range(0, rows, 8):
        for bx in range(0, sb, 16):
            for y in range(8):
                o += lin[(by + y) * sb + bx:(by + y) * sb + bx + 16]
    return bytes(o)


def shot(name, nib):
    run = warp.psp.Run(warp.psp.find_emu(None), iso, str(out / "run"), state=state)
    run.ws.s.settimeout(120)
    hits = set()
    for base in range(0x08800000, 0x0A000000, 0x100000):
        m = run.ws.mem(base, min(0x100000 + 64, 0x0A000000 - base))
        k = m.find(raw[64:128])
        while k >= 0:
            hits.add(base + k - 64)
            k = m.find(raw[64:128], k + 1)
    lin = bytearray(sb * rows)
    for y in range(rows):
        for xb in range(sb):
            lin[y * sb + xb] = IDX[nib(2 * xb, y) % 14] | IDX[nib(2 * xb + 1, y) % 14] << 4
    for a in hits:
        warp.poke(run, a, swizzle(lin))
    us = run.ws.call("cpu.status")["us"]
    run.ws.events.clear()
    run.ws.call("cpu.runUntilTime", us=us + 10 * round(warp.psp.FRAME_US))
    while run.ws.call("cpu.status")["us"] < us + 9 * warp.psp.FRAME_US:
        run.ws.wait("cpu.stepping")
    p = out / f"{name}.png"
    run.shot(str(p.resolve()))
    run.close()
    print(name, "texture at", [hex(a) for a in sorted(hits)])
    return np.array(Image.open(p).convert("RGB")).astype(int)


inv = {grey[i]: k for k, i in enumerate(IDX)}


def code(px):
    best = min(inv, key=lambda v: abs(v - int(px[0])))
    return inv[best] if abs(best - int(px[0])) < 6 else None


F = shot("fill", lambda x, y: 13)  # brightest grey
Y = shot("code_y", lambda x, y: y)
X = shot("code_x", lambda x, y: x)
lab, n = ndimage.label(F.max(2) > 200)  # above the screen's own grey bars
for ys, xs in ndimage.find_objects(lab):
    if (ys.stop - ys.start) * (xs.stop - xs.start) < 50:
        continue
    cx, cy = (xs.start + xs.stop) // 2, (ys.start + ys.stop) // 2
    yc = [code(Y[y, cx]) for y in range(ys.start, ys.stop)]
    xc = [code(X[cy, x]) for x in range(xs.start, xs.stop)]
    print(f"screen {xs.start},{ys.start},{xs.stop - xs.start},{ys.stop - ys.start}: source y = {yc[0]} mod 14 .. "
          f"{len(yc)} rows, x = {xc[0]} mod 14 .. {len(xc)} cols (match against the sprite's ink to pick the multiple)")
