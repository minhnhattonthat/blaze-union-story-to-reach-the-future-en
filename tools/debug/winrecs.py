"""Dump live text windows and their glyph records from a savestate. usage: winrecs.py STATE [--iso ISO] [--max 40]
Window pool: 16 structs of 0x9C at segment 1 + 0x652C0; record 0x24 bytes (docs/re/text.md, Printer)."""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import warp

ap = argparse.ArgumentParser()
ap.add_argument("state")
ap.add_argument("--iso", default=warp.ISO)
ap.add_argument("--max", type=int, default=40)
a = ap.parse_args()
run = warp.psp.Run(warp.psp.find_emu(None), a.iso, "work/qa/winrecs", state=a.state)
try:
    pool = warp.SEG1 + 0x652C0
    for i in range(16):
        w = run.ws.mem(pool + i * 0x9C, 0x9C)
        flags = struct.unpack_from("<I", w, 0x34)[0]
        if not flags & 1:
            continue
        x, y = struct.unpack_from("<2h", w)
        recs = struct.unpack_from("<I", w, 0x14)[0]
        cols, rows, cw, ch = struct.unpack_from("<4h", w, 0x18)
        spx, spy, ox, oy = struct.unpack_from("<4h", w, 8)
        print(f"win {i} at {x},{y} cols {cols} rows {rows} cell {cw}x{ch} sp {spx},{spy} off {ox},{oy} flags {flags:#x}")
        if not recs:
            continue
        d = run.ws.mem(recs, cols * rows * 0x24)
        shown = 0
        for j in range(cols * rows):
            r = d[j * 0x24:(j + 1) * 0x24]
            color, tex = struct.unpack_from("<I", r, 8)[0], struct.unpack_from("<I", r, 0x14)[0]
            if not color >> 24 or not tex:
                continue
            rx, ry, rw, rh = struct.unpack_from("<4h", r)
            sx, sy, sw, sh = struct.unpack_from("<4h", r, 0xC)
            fl = struct.unpack_from("<H", r, 0x1E)[0]
            print(f"  slot {j // cols}:{j % cols} x {rx} y {ry} {rw}x{rh} src {sx},{sy} {sw}x{sh} tex {tex:#x} color {color:#x} fl {fl:#x}")
            shown += 1
            if shown >= a.max:
                break
finally:
    run.close()
