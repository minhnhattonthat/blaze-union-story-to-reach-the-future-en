"""Issue 6: Morale Recovery with every item owned and morale full, circle on item N shows the CAUTION box (0xC4150).
usage: caution_probe.py ISO TAG N [log|rows1]. Shots work/qa/i6/TAG_msg*.png. log: print each glyph record index the printer
stores against the window's capacity (any index >= cap is a heap overflow); rows1: force the window to 1 row first (tests the
vwf newline guard). N=4 is the Blue Apple at 1_02_A."""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import scenes
import warp

iso, tag = sys.argv[1], sys.argv[2]
OUT = warp.ROOT / "work/qa/i6"


def give(run):  # every item owned: bits at save+0xC4 (0x533C), 0x114's count at save+0xE7
    sv = warp.u32(run, warp.SAVE_PTR)
    warp.poke(run, sv + 0xC4, b"\xff" * 0x23 + b"\x05")


steps = scenes.PREP + [(give,), (scenes.press, "right"), (scenes.wait, 120)]
run = warp.psp.Run(warp.psp.find_emu(None), iso, str(OUT / "run"))
B = warp.BASE
try:
    for fn, *args in steps:
        fn(run, *args)
    print("mode", warp.u32(run, warp.MODE))
    run.ws.call("cpu.breakpoint.add", address=B + 0xE1B0C, enabled=True)
    run.ws.events.clear()
    run.ws.call("cpu.runUntilTime", us=run.ws.call("cpu.status")["us"] + 2000000)
    run.ws.wait("cpu.stepping")
    s0 = run.ws.call("cpu.getAllRegs")["categories"][0]["uintValues"][16]
    run.ws.call("cpu.breakpoint.remove", address=B + 0xE1B0C)
    h = lambda o: struct.unpack("<H", run.ws.mem(s0 + o, 2))[0]
    print("s0", hex(s0), "items", h(0x47c), "morale", h(0x482), h(0x484))
    warp.poke(run, s0 + 0x482, struct.pack("<H", h(0x484)))
    scenes.press(run, *["down"] * int(sys.argv[3]), gap=20)
    warp.poke(run, s0 + 0x482, struct.pack("<H", h(0x484)))
    warp.run_to(run, run.frame() + 10)
    if len(sys.argv) > 4:  # log every glyph record the printer stores while the CAUTION box prints
        run.ws.call("cpu.breakpoint.add", address=B + 0xC4150, enabled=True)
        run.press({"circle"})
        run.ws.events.clear()
        run.ws.call("cpu.runUntilTime", us=run.ws.call("cpu.status")["us"] + 1000000)
        run.ws.wait("cpu.stepping")
        print("at", hex(run.ws.call("cpu.status")["pc"] - B))
        run.ws.call("cpu.breakpoint.remove", address=B + 0xC4150)
        if sys.argv[4] == "rows1":  # window made, text not yet printed: one row, so the second line is past the last row
            run.ws.call("cpu.breakpoint.add", address=B + 0xC41A0, enabled=True)
            run.ws.events.clear()
            run.ws.call("cpu.runUntilTime", us=run.ws.call("cpu.status")["us"] + 2000000)
            run.ws.wait("cpu.stepping")
            run.ws.call("cpu.breakpoint.remove", address=B + 0xC41A0)
            r =run.ws.call("cpu.getAllRegs")["categories"][0]["uintValues"]
            win = warp.u32(run, r[16])  # s0 = the box object, [s0] = window
            warp.poke(run, win + 0x1A, struct.pack("<h", 1))
            print("rows forced to 1 on window", hex(win))
        for a in (0x9EC34, 0xC41C8):
            run.ws.call("cpu.breakpoint.add", address=B + a, enabled=True)
        for _ in range(200):
            run.ws.events.clear()
            run.ws.call("cpu.runUntilTime", us=run.ws.call("cpu.status")["us"] + 2000000)
            run.ws.wait("cpu.stepping")
            pc = run.ws.call("cpu.status")["pc"] - B
            r = run.ws.call("cpu.getAllRegs")["categories"][0]["uintValues"]
            if pc == 0xC41C8:
                break
            s3 = r[19]
            buf = warp.u32(run, s3 + 0x14)
            cols, rows = struct.unpack("<hh", run.ws.mem(s3 + 0x18, 4))
            print("rec", hex(r[18]), "idx", (r[18] - buf) // 0x24, "cols", cols, "rows", rows, "cap", cols * rows, "fp", r[30], flush=True)
        for a in (0x9EC34, 0xC41C8):
            run.ws.call("cpu.breakpoint.remove", address=B + a)
        run.press(set())
    for i in range(6):
        if i == 0:
            scenes.press(run, "circle", gap=4)
        warp.run_to(run, run.frame() + 15)
        run.shot(str(OUT / f"{tag}_msg{i}.png"))
        print("alive", i, "mode", warp.u32(run, warp.MODE), flush=True)
    warp.run_to(run, run.frame() + 600)
    print("alive after 10 s, mode", warp.u32(run, warp.MODE))
    run.shot(str(OUT / f"{tag}_after.png"))
except (EOFError, UnicodeDecodeError, OSError, ValueError) as e:
    print("ended:", type(e).__name__, e)
finally:
    run.close()
