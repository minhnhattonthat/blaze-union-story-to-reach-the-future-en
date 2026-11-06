"""Run a scene's steps, then log every hit of code breakpoints until the emulator ends or the run times out: for a crash in a
scene that needs its own setup. usage: bptrace.py SCENE SKIP VADDR[,VADDR..] [--iso ISO] [--max 200]
SKIP = how many of the scene's last steps run under the breakpoints (they replace those steps with free running)."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scenes
import warp

ap = argparse.ArgumentParser()
ap.add_argument("scene")
ap.add_argument("skip", type=int)
ap.add_argument("addrs", type=lambda s: [int(x, 16) for x in s.split(",")])
ap.add_argument("--iso", default=warp.ISO)
ap.add_argument("--max", type=int, default=200)
ap.add_argument("--us", type=int, default=20000000)
a = ap.parse_args()
steps = scenes.SCENES[a.scene][0]
run = warp.psp.Run(warp.psp.find_emu(None), a.iso, str(warp.ROOT / "work/qa/bptrace"))
try:
    for fn, *args in steps[:-a.skip]:
        fn(run, *args)
    print("mode", warp.u32(run, warp.MODE))
    for s in a.addrs:
        run.ws.call("cpu.breakpoint.add", address=warp.BASE + s, enabled=True)
    for _ in range(a.max):
        run.ws.events.clear()
        run.ws.call("cpu.runUntilTime", us=run.ws.call("cpu.status")["us"] + a.us)
        run.ws.wait("cpu.stepping")
        st = run.ws.call("cpu.status")
        r = run.ws.call("cpu.getAllRegs")["categories"][0]["uintValues"]
        print(hex(st["pc"] - warp.BASE), "ra", hex((r[31] - warp.BASE) & 0xFFFFFFFF), "a0-3", [hex(x) for x in r[4:8]], "t0-1", hex(r[8]), hex(r[9]), "s0", hex(r[16]), flush=True)
    print("no end")
except (EOFError, UnicodeDecodeError, OSError, ValueError) as e:
    print("ended:", type(e).__name__)
finally:
    run.close()
