"""Rewrite the decrypted EBOOT: patch segment 0 in place, add a third PT_LOAD with code and text, add relocations.
The result is a plain ELF that PPSSPP and CFW load (docs/re/text.md). File offset of segment 0 = vaddr + SEG0, RAM = base + vaddr."""
import struct

SEG0 = 0x74  # file offset of segment 0 in the dump
R_32, R_26, R_HI16, R_LO16 = 2, 4, 5, 6  # PSP relocation types, segment 0 relative: info = type | ofsbase << 8 | addrbase << 16
SHF_WAX = 7
SHT_PSPREL = 0x700000A0


def rel_offsets(elf):
    """Every word a relocation entry patches: a hook must not overwrite one by accident."""
    shoff, shnum = struct.unpack_from("<I", elf, 32)[0], struct.unpack_from("<H", elf, 48)[0]
    out = set()
    for i in range(shnum):
        s = struct.unpack_from("<10I", elf, shoff + i * 40)
        if s[1] == SHT_PSPREL:
            for off, info in struct.iter_unpack("<II", elf[s[4]:s[4] + s[5]]):
                if not (info >> 8) & 0xFF:  # offset based on segment 0
                    out.add(off)
    return out


class Eboot:
    def __init__(self, elf, seg_vaddr):
        self.elf = bytearray(elf)
        self.vaddr = seg_vaddr  # the new segment's vaddr
        self.blob = bytearray()
        self.rels = []
        self.relocated = rel_offsets(elf)
        self.writes = []  # (vaddr, old bytes, new bytes): tools/verify_build.py runs romdiff over them

    def word(self, vaddr):
        return struct.unpack_from("<I", self.elf, SEG0 + vaddr)[0]

    def put(self, vaddr, data):
        at = SEG0 + vaddr
        self.writes.append((vaddr, bytes(self.elf[at:at + len(data)]), bytes(data)))
        self.elf[at:at + len(data)] = data

    def hook(self, vaddr, expect, word, reloc=None):
        """Replace one instruction, checking the original: a different dump fails at build time, not in game."""
        assert self.word(vaddr) == expect, f"{vaddr:#x}: {self.word(vaddr):#x}"
        assert vaddr not in self.relocated, f"{vaddr:#x} carries a relocation"
        self.put(vaddr, word.to_bytes(4, "little"))
        if reloc is not None:
            self.rels.append((vaddr, reloc))

    def append(self, data, align=1):
        """Add data to the new segment. -> its vaddr."""
        self.blob += bytes(-len(self.blob) % align)
        p = self.vaddr + len(self.blob)
        self.blob += data
        return p

    def serialize(self):
        """Segment 0 moves 0x20 down to make room for a third program header; everything after it shifts with it."""
        e = self.elf
        self.blob += bytes(-len(self.blob) % 4)  # PPSSPP asserts on a section whose end isn't word-aligned
        phoff, shoff = struct.unpack_from("<II", e, 28)
        phnum, shnum = struct.unpack_from("<H", e, 44)[0], struct.unpack_from("<H", e, 48)[0]
        assert phoff == 0x34 and phnum == 2, (phoff, phnum)
        sects = [list(struct.unpack_from("<10I", e, shoff + i * 40)) for i in range(shnum)]
        phs = [list(struct.unpack_from("<8I", e, phoff + i * 32)) for i in range(2)]
        for p in phs:
            p[1] += 0x20
        for s in sects:
            if s[4] >= SEG0 and s[1]:
                s[4] += 0x20
        body = bytes(e[SEG0:shoff]) + bytes(e[shoff + shnum * 40:])  # drop the old section table
        cut = shoff + shnum * 40 - shoff  # sections stored after the old table move back by its size
        for s in sects:
            if s[4] - 0x20 >= shoff + shnum * 40:
                s[4] -= cut
        pos = SEG0 + 0x20 + len(body)
        pad = -pos % 64
        seg_off = pos + pad
        rel_off = seg_off + len(self.blob) + (-len(self.blob) % 4)
        rel = b"".join(struct.pack("<II", off, typ) for off, typ in self.rels)
        name_text = next(s[0] for s in sects if s[3] == 0 and s[1] == 1)  # any existing name will do
        sects.append([name_text, 1, SHF_WAX, self.vaddr, seg_off, len(self.blob), 0, 0, 64, 0])
        sects.append([name_text, SHT_PSPREL, 0, 0, rel_off, len(rel), 0, 1, 4, 8])
        new_shoff = rel_off + len(rel)
        out = bytearray(e[:0x34])
        struct.pack_into("<II", out, 28, 0x34, new_shoff)
        struct.pack_into("<H", out, 44, 3)
        struct.pack_into("<H", out, 48, len(sects))
        for p in phs:
            out += struct.pack("<8I", *p)
        out += struct.pack("<8I", 1, seg_off, self.vaddr, 0, len(self.blob), len(self.blob), 7, 64)
        assert len(out) == SEG0 + 0x20
        out += body + bytes(pad) + self.blob
        out += bytes(rel_off - len(out)) + rel
        for s in sects:
            out += struct.pack("<10I", *s)
        return bytes(out)
