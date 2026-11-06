"""RE helper over PPSSPP's WebSocket debugger, using the skill's psp.py.
usage:
  ppdbg.py dump STATE OUT.bin                     write user RAM 0x08000000-0x0A000000
  ppdbg.py find STATE SJIS_TEXT                   list RAM addresses holding the text (Shift-JIS and UTF-16LE)
  ppdbg.py mods STATE                             list loaded modules
  ppdbg.py watch STATE ADDR SIZE [FRAMES] [--press BTN] [--write]
        memory breakpoint on read (or write): each hit prints pc, ra, a0-a3 and the bytes around pc, up to 20 hits
ISO defaults to the pinned dump; PPSSPP states need the same image they were saved on (env BU_ISO overrides)."""
import base64
import json
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
RAM = 0x08000000
RAM_END = 0x0A000000


def start(state):
    return psp.Run(psp.find_emu(None), ISO, str(ROOT / "work/qa/ppdbg"), state=state)


def read_ram(run):
    out = bytearray()
    for a in range(RAM, RAM_END, 0x100000):
        out += run.ws.mem(a, 0x100000)
    return bytes(out)


def main():
    cmd, state = sys.argv[1], sys.argv[2]
    run = start(state)
    try:
        if cmd == "dump":
            Path(sys.argv[3]).write_bytes(read_ram(run))
        elif cmd == "find":
            d = read_ram(run)
            for enc in ("cp932", "utf-16le"):
                needle = sys.argv[3].encode(enc)
                p = d.find(needle)
                while p >= 0:
                    print(enc, hex(RAM + p), d[p - 8:p + 40].hex())
                    p = d.find(needle, p + 1)
        elif cmd == "peek":  # peek STATE ADDR SIZE
            b = run.ws.mem(int(sys.argv[3], 16), int(sys.argv[4], 16))
            print(" ".join(hex(x) for x in struct.unpack(f"<{len(b) // 4}I", b[:len(b) & ~3])))
        elif cmd == "mods":
            for m in run.ws.call("hle.module.list")["modules"]:
                print(hex(m["address"]), hex(m["size"]), m["name"])
        elif cmd == "watch":
            addr, size = int(sys.argv[3], 16), int(sys.argv[4], 16)
            frames = int(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5].isdigit() else 60
            write = "--write" in sys.argv
            run.ws.call("memory.breakpoint.add", address=addr, size=size, enabled=True, log=False,
                        read=not write, write=write, change=False)
            if "--press" in sys.argv:
                run.press({sys.argv[sys.argv.index("--press") + 1]})
            hits = 0
            for _ in range(20):
                run.ws.call("cpu.runUntilTime", us=run.base + round(frames * psp.FRAME_US))
                ev = run.ws.wait("cpu.stepping")
                regs = {r["name"]: r["uintValue"] for c in run.ws.call("cpu.getAllRegs")["categories"]
                        for r in c["registers"] if c["name"] == "GPR"} if False else None
                st = run.ws.call("cpu.status")
                if st["us"] >= run.base + round(frames * psp.FRAME_US) - 100:
                    break
                hits += 1
                print(json.dumps(ev), st)
                pc = st.get("pc", 0)
                allr = run.ws.call("cpu.getAllRegs")["categories"][0]["uintValues"]
                print(" pc", hex(pc), "ra", hex(allr[31]), "a0-3", [hex(x) for x in allr[4:8]], "s0-2", [hex(x) for x in allr[16:19]])
            print("hits", hits)
    finally:
        run.close()


if __name__ == "__main__":
    main()
