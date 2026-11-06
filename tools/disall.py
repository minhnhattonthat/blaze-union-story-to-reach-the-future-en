"""Disassemble work/exe/code.bin 0..0x1D0000 (segment 0 code) to work/exe/dis.txt with resolved lui/addiu addresses, for grep.
usage: disall.py  (needs capstone; ~20 s)"""
import capstone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
code = (ROOT / "work/exe/code.bin").read_bytes()[:0x1D0000]
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN)
md.skipdata = True
lui = {}  # reg -> (value, addr); shortcut: linear scan, a branch target can show a stale lui, good enough for grep
with open(ROOT / "work/exe/dis.txt", "w") as f:
    for i in md.disasm(code, 0):
        op, a, note = i.op_str, i.address, ""
        parts = [p.strip() for p in op.split(",")]
        if i.mnemonic == "lui":
            lui[parts[0]] = int(parts[1], 0) << 16
        elif "(" in op and len(parts) == 2:
            off, base = parts[1].rstrip(")").split("(")
            if base in lui and not off.startswith("$"):
                note = f"  ; [{(lui[base] + int(off or '0', 0)) & 0xFFFFFFFF:#x}]"
        elif i.mnemonic in ("addiu", "ori") and len(parts) == 3 and parts[1] in lui:
            note = f"  ; ={(lui[parts[1]] + int(parts[2], 0)) & 0xFFFFFFFF:#x}"
        f.write(f"{a:06x} {i.mnemonic} {op}{note}\n")
