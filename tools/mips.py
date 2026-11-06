"""Small MIPS assembler for the EBOOT hooks: only the instructions they use. asm(text, base) -> (bytes, {label: address}).
Syntax: `label:`, `op a, b, c`, `lw $t0, 8($s1)`, `#` comments, `.byte`-less: data goes next to the code from Python."""
import re

REG = {n: i for i, n in enumerate(
    "zero at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split())}
R3 = {"addu": 0x21, "subu": 0x23, "and": 0x24, "or": 0x25, "slt": 0x2A, "sltu": 0x2B}  # rd, rs, rt
I3 = {"addiu": 9, "slti": 10, "sltiu": 11, "andi": 12, "ori": 13}  # rt, rs, imm
MEM = {"lb": 0x20, "lh": 0x21, "lw": 0x23, "lbu": 0x24, "lhu": 0x25, "sb": 0x28, "sh": 0x29, "sw": 0x2B}
SHIFT = {"sll": 0, "srl": 2, "sra": 3}  # rd, rt, shamt


def reg(s):
    return REG[s.strip().lstrip("$")]


def num(s):
    return int(s.strip(), 0)


def encode(op, a, addr, labels):
    def target(s):
        return labels[s] if s in labels else num(s)

    def branch(s):
        off = target(s) - addr - 4
        assert off % 4 == 0 and -0x20000 <= off < 0x20000, (op, s, off)
        return (off >> 2) & 0xFFFF

    if op == "nop":
        return 0
    if op == "move":
        return reg(a[1]) << 21 | reg(a[0]) << 11 | 0x21
    if op in R3:
        return reg(a[1]) << 21 | reg(a[2]) << 16 | reg(a[0]) << 11 | R3[op]
    if op in I3:
        return I3[op] << 26 | reg(a[1]) << 21 | reg(a[0]) << 16 | num(a[2]) & 0xFFFF
    if op in SHIFT:
        return reg(a[1]) << 16 | reg(a[0]) << 11 | num(a[2]) << 6 | SHIFT[op]
    if op in MEM:
        m = re.fullmatch(r"(.*)\((.*)\)", a[1].strip())
        return MEM[op] << 26 | reg(m[2]) << 21 | reg(a[0]) << 16 | (num(m[1] or "0") & 0xFFFF)
    if op == "lui":
        return 15 << 26 | reg(a[0]) << 16 | num(a[1]) & 0xFFFF
    if op == "mult":
        return reg(a[0]) << 21 | reg(a[1]) << 16 | 0x18
    if op == "mflo":
        return reg(a[0]) << 11 | 0x12
    if op == "jr":
        return reg(a[0]) << 21 | 8
    if op == "jal":
        return 3 << 26 | (target(a[0]) >> 2) & 0x3FFFFFF
    if op == "beq":
        return 4 << 26 | reg(a[0]) << 21 | reg(a[1]) << 16 | branch(a[2])
    if op == "bne":
        return 5 << 26 | reg(a[0]) << 21 | reg(a[1]) << 16 | branch(a[2])
    if op == "beqz":
        return 4 << 26 | reg(a[0]) << 21 | branch(a[1])
    if op == "bnez":
        return 5 << 26 | reg(a[0]) << 21 | branch(a[1])
    if op == "blez":
        return 6 << 26 | reg(a[0]) << 21 | branch(a[1])
    if op == "bgtz":
        return 7 << 26 | reg(a[0]) << 21 | branch(a[1])
    if op == "bltz":
        return 1 << 26 | reg(a[0]) << 21 | branch(a[1])
    if op == "bgez":
        return 1 << 26 | reg(a[0]) << 21 | 1 << 16 | branch(a[1])
    if op == "bal":
        return 1 << 26 | 0x11 << 16 | branch(a[0])
    raise ValueError(f"unknown op {op}")


def asm(text, base=0):
    """Two passes: every instruction is 4 bytes, so labels are known after the first."""
    lines, labels = [], {}
    for raw in text.splitlines():
        s = raw.split("#")[0].strip()
        while ":" in s:
            name, s = s.split(":", 1)
            labels[name.strip()] = base + len(lines) * 4
            s = s.strip()
        if s:
            lines.append(s)
    out = bytearray()
    for i, s in enumerate(lines):
        op, _, rest = s.partition(" ")
        out += encode(op, [x.strip() for x in rest.split(",") if x.strip()], base + i * 4, labels).to_bytes(4, "little")
    return bytes(out), labels
