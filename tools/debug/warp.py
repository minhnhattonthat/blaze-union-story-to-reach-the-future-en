"""Reach a stage or screen from a cold boot by poking the game's own requests. No save, no playthrough.
usage: warp.py NAME|INDEX|- --out DIR [--state-in S] [--route "60 -;6 circle"] [--mash circle,start] [--frames N] [--every N]
                [--state-out S] [--iso ISO]
NAME is a stage from the table at vaddr 0x286EC4 (1_01_A ..), "-" boots without warping. Every mode change gets a shot
(mNNNNNN_MM.png) and a log line. Layout and findings: docs/re/debug.md."""
import argparse
import base64
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SCRIPTS

sys.path.insert(0, SCRIPTS)
import psp

ISO = os.environ.get("BU_ISO") or str(ROOT / "rom/Blaze Union - Story to Reach The Future (Japan).iso")
BASE = 0x08804000  # RAM = BASE + vaddr, verified in docs/re/README.md
SEG1 = BASE + 0x2BFCA0  # lui values below 0x0A are relative to segment 1 (verified: mode reads 7 here in a dialogue)
REQ = BASE + 0x2707F8  # request flags
SAVE_PTR = BASE + 0x27167C  # -> game state; +0x19A is the current stage (s16)
MODE = SEG1 + 0x808B4  # top-level mode: index into the handler table at vaddr 0x270810
REQ_RESTART = 0x100  # mode 0 (vaddr 0x1658, full re-init) with this flag: a9b60(save.stage, 1, 0), then mode 7
DBG_STAGE, DBG_FLAGS = BASE + 0x270800, BASE + 0x270950
TABLE, RECORD, COUNT = 0x286EC4, 28, 153


def run_to(self, f):
    """psp.Run.run_to, surviving a game clock change (222 to 266 MHz at battle start). cpu.status us is ticks / clockHz, so
    it jumps when the clock does; the stock loop then waits forever for a stop that already came. Keep frames continuous."""
    target = self.base + round(f * psp.FRAME_US)
    st = self.ws.call("cpu.status")
    if target <= st["us"] + 100:
        return
    self.ws.events.clear()  # an older stop must not count as this one
    self.ws.call("cpu.runUntilTime", us=target)
    self.ws.wait("cpu.stepping")
    now = self.ws.call("cpu.status")
    if now["clockHz"] != st["clockHz"]:
        self.base += now["us"] - round(now["ticks"] * 1e6 / st["clockHz"])


psp.Run.run_to = run_to


def stages():
    code = (ROOT / "work/exe/code.bin").read_bytes()
    out = []
    for i in range(COUNT):
        q = struct.unpack_from("<I", code, TABLE + i * RECORD + 12)[0]
        out.append(code[q:code.index(0, q)].decode())
    return out


def u32(run, a):
    return struct.unpack("<I", run.ws.mem(a, 4))[0]


def poke(run, a, data):
    run.ws.call("memory.write", address=a, base64=base64.b64encode(data).decode())


def warp(run, index, card=True):
    """card: the leftover stage-start path in mode 0 (vaddr 0x1B04): flag 0x10000 at 0x270950, stage at 0x270800, plays
    the chapter card. Else the retry path at vaddr 0x2A50 (flag 0x100, stage in the save), straight to the event."""
    save = u32(run, SAVE_PTR)
    assert 0x08800000 <= save < 0x0A000000, hex(save)
    poke(run, save + 0x19A, struct.pack("<h", index))
    if card:
        poke(run, DBG_STAGE, struct.pack("<I", index))
        poke(run, DBG_FLAGS, struct.pack("<I", u32(run, DBG_FLAGS) | 0x10000))
    else:
        poke(run, REQ, struct.pack("<I", u32(run, REQ) | REQ_RESTART))
    poke(run, MODE, struct.pack("<I", 0))


def boot(run):
    """Cold boot to the title flow: mode 2 is reached near frame 60, settle first."""
    f = 0
    while u32(run, MODE) != 2:
        f += 10
        run.run_to(f)
        assert f < 1200, "mode 2 not reached"
    run.run_to(f + 240)


def drive(run, frames, every, route=(), mash=False, step=10, mash_from=0):
    """Run to frame FRAMES in STEP increments, logging mode changes. Returns the mode log [(frame, mode)]."""
    log, mode, f = [], None, run.frame()
    mash_from += f
    keys = sorted((lo + f, set(k)) for lo, k in route)
    while f < frames:
        f += step
        due = [k for lo, k in keys if lo <= f]
        press = due[-1] if due else set()
        if mash and f >= mash_from and (f // step) % 4 == 0:
            press = {mash[(f // step // 4) % len(mash)]}
        run.press(press)
        run.run_to(f)
        m = u32(run, MODE)
        if m != mode:
            log.append((f, m))
            print(f"frame {f} mode {m}", flush=True)
            if f > 300:  # before the first rendered frame gpu.buffer.screenshot fails
                run.shot(f"m{f:06d}_{m:02d}.png")
            mode = m
        if every and f % every == 0:
            run.shot(f"f{f:06d}.png")
    return log


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage")
    ap.add_argument("--out", required=True)
    ap.add_argument("--state-in")
    ap.add_argument("--state-out")
    ap.add_argument("--route", default="")
    ap.add_argument("--mash", type=lambda s: s.split(","), default=[], help="buttons pressed in turn, e.g. circle,start")
    ap.add_argument("--mash-from", type=int, default=0, help="start mashing this many frames in")
    ap.add_argument("--mode", type=int, help="top-level mode to poke before the run; see docs/re/debug.md first")
    ap.add_argument("--frames", type=int, default=600)
    ap.add_argument("--every", type=int, default=0)
    ap.add_argument("--iso", default=ISO)
    ap.add_argument("--no-card", action="store_true", help="retry path: straight to the event, no chapter card")
    ap.add_argument("--poke", action="append", default=[], type=lambda s: (int(s.split("=")[0], 16), bytes.fromhex(s.split("=")[1])),
                    help="RAMADDR=HEXBYTES written once before the run, repeatable")
    ap.add_argument("--req", type=lambda s: int(s, 0), default=0, help="request flag for mode 0, e.g. 0x200 (ending)")
    ap.add_argument("--var", action="append", default=[], type=lambda s: tuple(int(x, 0) for x in s.split("=")),
                    help="story variable N=V, repeatable")
    a = ap.parse_args()
    names = stages()
    route, acc = [], 0
    for n, k in psp.parse_route(a.route):
        route.append((acc, k))
        acc += n
    route.append((acc, set()))
    run = psp.Run(psp.find_emu(None), a.iso, a.out, state=a.state_in)
    try:
        if a.stage != "-":
            index = int(a.stage) if a.stage.isdigit() else names.index(a.stage)
            if not a.state_in:
                boot(run)
            print("stage", names[index], index, "mode before", u32(run, MODE))
            warp(run, index, card=not a.no_card)
        if a.req or a.var:
            if not a.state_in:
                boot(run)
            save = u32(run, SAVE_PTR)
            for n, v in a.var:
                poke(run, save + 0x20 + n, bytes([v]))  # story variable, see 0x4FE4
            if a.req:
                poke(run, REQ, struct.pack("<I", u32(run, REQ) | a.req))
                poke(run, MODE, struct.pack("<I", 0))
        for addr, data in a.poke:
            poke(run, addr, data)
        if a.mode is not None:
            poke(run, MODE, struct.pack("<I", a.mode))
        drive(run, run.frame() + a.frames, a.every, route, a.mash, mash_from=a.mash_from)
        run.shot("final.png")
        if a.state_out:
            run.save_state(a.state_out)
    finally:
        run.close()


if __name__ == "__main__":
    main()
