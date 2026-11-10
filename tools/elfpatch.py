"""Rewrite the decrypted EBOOT: patch segment 0 in place, append code and text to segment 1 past its .bss, add relocations.
The result is a plain ELF that PPSSPP and CFW load (docs/re/text.md). File offset of segment 0 = vaddr + SEG0, RAM = base + vaddr."""
import struct

SEG0 = 0x74  # file offset of segment 0 in the dump
R_32, R_26, R_HI16, R_LO16 = 2, 4, 5, 6  # PSP relocation types, segment 0 relative: info = type | ofsbase << 8 | addrbase << 16
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
        """Gloria Union's layout, which loads on a real PSP/Vita (issue #4): the program headers stay as they are, segment 1
        gets file bytes for its .bss (zeros) plus the blob; the sections stored after it (.shstrtab, .rel*) are copied after
        it in file order, the section table goes last. New relocations go at the end of the last .rel section, those
        patching segment 1 relative to segment 1. Segment 0 and p_paddr (sceModuleInfo's file offset) do not move."""
        e = self.elf
        self.blob += bytes(-len(self.blob) % 4)  # PPSSPP asserts on a section whose end isn't word-aligned
        shoff, shnum = struct.unpack_from("<I", e, 32)[0], struct.unpack_from("<H", e, 48)[0]
        assert struct.unpack_from("<I", e, 28)[0] == 0x34 and struct.unpack_from("<H", e, 44)[0] == 2
        ph1 = list(struct.unpack_from("<8I", e, 0x34 + 32))
        s1v, s1o, s1f = ph1[2], ph1[1], ph1[4]
        assert self.vaddr >= s1v + ph1[5] and self.vaddr % 16 == 0, "the blob goes past segment 1's .bss"
        seg1 = bytes(e[s1o:s1o + s1f]) + bytes(self.vaddr - s1v - s1f) + self.blob
        ph1[4] = ph1[5] = len(seg1)
        rel = b"".join(struct.pack("<II", v - s1v, t | 1 << 8) if v >= s1v else struct.pack("<II", v, t)
                       for v, t in self.rels)
        sects = [list(struct.unpack_from("<10I", e, shoff + i * 40)) for i in range(shnum)]
        tail = s1o + s1f
        stored = sorted((s for s in sects if s[1] not in (0, 8) and s[4] >= tail), key=lambda s: s[4])
        assert all(s[4] + s[5] <= tail for s in sects if s[1] not in (0, 8) and s[4] < tail)
        last = max((s for s in stored if s[1] == SHT_PSPREL), key=lambda s: s[4])
        out = bytearray(e[:s1o]) + seg1
        for s in stored:
            out += bytes(-len(out) % max(s[8], 1))
            data = bytes(e[s[4]:s[4] + s[5]]) + (rel if s is last else b"")
            s[4] = len(out)
            out += data
        last[5] += len(rel)
        out += bytes(-len(out) % 4)
        struct.pack_into("<I", out, 32, len(out))
        struct.pack_into("<8I", out, 0x34 + 32, *ph1)
        out += b"".join(struct.pack("<10I", *s) for s in sects)
        return bytes(out)
