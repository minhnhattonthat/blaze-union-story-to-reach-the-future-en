"""Find where a warp ends the emulator: breakpoints after every jal in a code range, printed in hit order until the debugger
drops. Run it again on the last call's target to drill down. PPSSPPHeadless ends without a word on a bad guest access.
usage: crashpc.py STAGE|- LO HI [--no-card] [--state-in S] [--var N=V].. [--mode M] [--max 400]
LO, HI: hex vaddrs (needs work/exe/dis.txt)."""
import argparse
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import warp

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("stage")
ap.add_argument("lo", type=lambda s: int(s, 16))
ap.add_argument("hi", type=lambda s: int(s, 16))
ap.add_argument("--no-card", action="store_true")
ap.add_argument("--state-in")
ap.add_argument("--var", action="append", default=[], type=lambda s: tuple(int(x, 0) for x in s.split("=")))
ap.add_argument("--mode", type=int)
ap.add_argument("--max", type=int, default=400)
a = ap.parse_args()
sites = {}
for line in (warp.ROOT / "work/exe/dis.txt").read_text().splitlines():
    m = re.match(r"(\w{6}) jalr? (\S+)", line)
    if m and a.lo <= int(m.group(1), 16) < a.hi:
        sites[int(m.group(1), 16) + 8] = m.group(2)
run = warp.psp.Run(warp.psp.find_emu(None), warp.ISO, str(warp.ROOT / "work/qa/crashpc"), state=a.state_in)
if not a.state_in:
    warp.boot(run)
if a.stage != "-":
    warp.warp(run, warp.stages().index(a.stage), card=not a.no_card)
save = warp.u32(run, warp.SAVE_PTR)
for n, v in a.var:
    warp.poke(run, save + 0x20 + n, bytes([v]))
if a.mode is not None:
    warp.poke(run, warp.MODE, struct.pack("<I", a.mode))
for s in sites:
    run.ws.call("cpu.breakpoint.add", address=warp.BASE + s, enabled=True)
try:
    for _ in range(a.max):
        run.ws.events.clear()
        run.ws.call("cpu.runUntilTime", us=run.ws.call("cpu.status")["us"] + 5000000)
        run.ws.wait("cpu.stepping")
        st = run.ws.call("cpu.status")
        pc = st["pc"] - warp.BASE
        regs = run.ws.call("cpu.getAllRegs")["categories"][0]["uintValues"]
        print(st["us"], hex(pc), "returned from", sites.get(pc, "?"), "v0", hex(regs[2]), flush=True)
    print("no end within --max hits")
except (EOFError, UnicodeDecodeError, OSError) as e:
    print("ended:", type(e).__name__)
run.close()
