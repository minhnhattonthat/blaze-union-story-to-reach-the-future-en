"""Does the third EBOOT segment survive in RAM? Compare it with the built EBOOT after a warp. usage: segcheck.py ISO [STAGE]"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import warp
import iso9660

warp.psp_iso = iso9660
iso = sys.argv[1]
stage = sys.argv[2] if len(sys.argv) > 2 else "1_01_A"
with open(iso, "rb") as f:
    _, lba, size, _ = next(e for e in warp.psp_iso.listing(f) if e[0] == "/PSP_GAME/SYSDIR/EBOOT.BIN")
    f.seek(lba * 2048)
    elf = f.read(size)
ph = struct.unpack_from("<8I", elf, 0x34 + 2 * 32)
off, vaddr, filesz = ph[1], ph[2], ph[4]
blob = elf[off:off + filesz]
run = warp.psp.Run(warp.psp.find_emu(None), iso, str(warp.ROOT / "work/qa/segcheck"))
try:
    warp.boot(run)
    warp.warp(run, warp.stages().index(stage))
    warp.drive(run, run.frame() + 600, 0, mash=["circle"])
    ram = run.ws.mem(warp.BASE + vaddr, filesz)
    bad = [i for i in range(0, filesz, 256) if ram[i:i + 256] != blob[i:i + 256]]
    print(f"segment {vaddr:#x} size {filesz:#x}: {len(bad)} of {filesz // 256} blocks differ", [hex(vaddr + b * 1) for b in bad[:6]])
    print("modules", [(hex(m["address"]), hex(m["size"]), m["name"]) for m in run.ws.call("hle.module.list")["modules"]][:6])
finally:
    run.close()
