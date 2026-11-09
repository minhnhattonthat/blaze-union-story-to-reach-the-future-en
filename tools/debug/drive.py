"""Drive a PPSSPP state (a player's, or one of ours) in relative steps, logging mode changes with a shot each.
emu.py and warp.drive go by cpu.status us from the load, which is ticks / clock: on a state with hours of play behind it the
game's 222/266 MHz switch at combat moves us by minutes and the run waits forever (emu.py) or counts negative frames. Steps
here are relative to the us of the moment, so they survive it. Exit 5 when the emulator ends (a guest crash).
usage: drive.py ISO STATE OUT FRAMES EVERY [--press F:KEY[+KEY],..] [--mash KEY[,KEY]] [--mash-from F] [--save-every N]"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import warp

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("iso")
ap.add_argument("state")
ap.add_argument("out")
ap.add_argument("frames", type=int)
ap.add_argument("every", type=int, help="shot every N frames, 0 = none")
ap.add_argument("--press", default="")
ap.add_argument("--mash", default="")
ap.add_argument("--mash-from", type=int, default=0)
ap.add_argument("--save-every", type=int, default=0)
a = ap.parse_args()
out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)
presses = {}
for p in filter(None, a.press.split(",")):
    f, k = p.split(":")
    presses[int(f)] = set(k.split("+"))
mash = a.mash.split(",") if a.mash else []
run = warp.psp.Run(warp.psp.find_emu(None), a.iso, str(out), state=a.state)
run.ws.s.settimeout(120)
STEP = 2
f, mode = 0, None
try:
    while f < a.frames:
        keys = set()
        for pf, k in presses.items():
            if pf <= f < pf + 6:
                keys = k
        if mash and f >= a.mash_from and (f // 6) % 6 == 0:
            keys = {mash[(f // 36) % len(mash)]}
        run.press(keys)
        run.ws.events.clear()
        us = run.ws.call("cpu.status")["us"]
        run.ws.call("cpu.runUntilTime", us=us + round(STEP * warp.psp.FRAME_US))
        run.ws.wait("cpu.stepping")
        f += STEP
        m = warp.u32(run, warp.MODE)
        if m != mode:
            print(f"frame {f} mode {m}", flush=True)
            run.shot(f"m{f:06d}_{m:02d}.png")
            mode = m
        if a.every and f % a.every == 0:
            run.shot(f"f{f:06d}.png")
        if a.save_every and f % a.save_every == 0:
            run.save_state(str(out / f"s{f:06d}.ppst"))
    run.shot("final.png")
    run.save_state(str(out / "final.ppst"))
    print("done", f)
except Exception as e:
    print("ENDED at frame", f, type(e).__name__, e, flush=True)
    sys.exit(5)
finally:
    run.close()
