"""Warp to every stage from a cold boot, each in its own emulator, and check it reached that stage.
usage: warp_all.py [--out work/qa/stages] [--jobs 8] [--frames 1200] [--iso ISO] [--states] [NAME..]
A stage passes when the game state holds its index, the mode is one the warp can land in (5/6 chapter or stage card,
7 event, 9/18-20 into prep) and the final shot is not flat. Shots: OUT/<name>.png; --states also writes work/states/<name>.ppst.
Exit 1 if any stage fails."""
import argparse
import shutil
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import warp

ROOT = warp.ROOT
CARD_MODES = (5, 6, 7, 9, 18, 19, 20)  # 18 on: with no key pressed the stage's event has ended and prep has begun
DEAD = {"1_05_B", "1_05_C"}  # record points at entries 1 and 2 of script 2153, which has only entry 0: never reached in the game


def one(name, a):
    """Returns (name, error or ''). Runs in a child process per stage: psp.Run owns one emulator."""
    cmd = [sys.executable, "-X", "utf8", __file__, "--child", name, "--out", a.out, "--frames", str(a.frames), "--iso", a.iso]
    cmd += ["--states"] if a.states else []
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    return name, "" if r.returncode == 0 else (r.stdout + r.stderr).strip().splitlines()[-1]


def child(name, a):
    out = Path(a.out) / "_run" / name
    shutil.rmtree(out, ignore_errors=True)
    names = warp.stages()
    run = warp.psp.Run(warp.psp.find_emu(None), a.iso, str(out))
    try:
        warp.boot(run)
        index = names.index(name)
        warp.warp(run, index)
        run.run_to(run.frame() + a.frames)
        save = warp.u32(run, warp.SAVE_PTR)
        got = struct.unpack("<h", run.ws.mem(save + 0x19A, 2))[0]
        mode = warp.u32(run, warp.MODE)
        shot = run.shot("final.png")
        shutil.copy(shot, Path(a.out) / f"{name}.png")
        if a.states:
            run.save_state(str(ROOT / "work/states" / f"{name}.ppst"))
        assert got == index, f"stage {got} != {index}"
        assert mode in CARD_MODES, f"mode {mode}"
        assert not warp.psp.blank(shot), "flat shot"
    finally:
        run.close()
    shutil.rmtree(out, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("names", nargs="*")
    ap.add_argument("--out", default=str(ROOT / "work/qa/stages"))
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--frames", type=int, default=1200)
    ap.add_argument("--iso", default=warp.ISO)
    ap.add_argument("--states", action="store_true")
    ap.add_argument("--child")
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    if a.child:
        child(a.child, a)
        return
    names = a.names or [n for n in warp.stages() if n not in DEAD]
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda n: one(n, a), names))
    bad = [r for r in res if r[1]]
    for n, e in bad:
        print("FAIL", n, e[:200])
    print(f"{len(res) - len(bad)}/{len(res)} stages ok")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
