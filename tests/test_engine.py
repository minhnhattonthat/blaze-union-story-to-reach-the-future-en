"""Engine pieces of the English build: assembler, FCT rebuild, EBOOT rewrite, marker text. Needs the unpacked work/ (skips on a clone)."""
import struct
import sys
from pathlib import Path

import capstone
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import elfpatch
import extract
import fct
import insert
import marker
import mips
import ptx
import vwf

work = pytest.mark.skipif(not (ROOT / "work/cpk/00003.bin").is_file(), reason="needs work/cpk")


def test_assembler_matches_capstone():
    src = """
    start:
        lw $s2, 0x14($s3)
        sh $a0, 0($s2)
        lbu $t7, -5($a1)
        addiu $sp, $sp, -16
        addu $t3, $v0, $a1
        sll $s5, $s5, 2
        srl $v0, $v0, 24
        mult $a0, $v1
        mflo $a1
        beqz $t7, start
        bnez $v0, start
        bal start
        jr $ra
        sltiu $t9, $t6, 96
        move $t8, $ra
    """
    code, _ = mips.asm(src, 0x1000)
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN)
    got = [f"{i.mnemonic} {i.op_str}".strip() for i in md.disasm(code, 0x1000)]
    assert len(got) == 15
    assert got[0] == "lw $s2, 0x14($s3)"
    assert got[2] == "lbu $t7, -5($a1)"
    assert got[9] == "beqz $t7, 0x1000"
    assert got[11] == "bal 0x1000"
    assert got[14] == "move $t8, $ra"


def test_item_line_breaks():
    w = {ord(c): 10 for c in "abc d"}
    assert vwf.breaks("aa bb cc dd", 2, 2, 20, w) == bytes([3, 6])
    assert vwf.breaks("aa bb", 2, 2, 50, w) == bytes([0, 0])
    assert vwf.breaks("aa bb cc dd", 1, 2, 20, w) == bytes([3])


def test_all_routines_assemble():
    code, labels = mips.asm(vwf.ROUTINES.replace("CELLS-enter_0", "0").replace("WIDTHS-advance_0", "0").replace("BASES-ascii_0", "0")
                            .replace("WIDTHS-count_0", "0"), 0x363000)
    assert {"enter", "store", "newline", "advance", "ascii", "layout_a", "layout_b", "count_init", "count_ascii"} <= set(labels)
    assert len(code) % 4 == 0


@work
def test_fct_rebuild_identity():
    d = (extract.CPK / "00003.bin").read_bytes()
    assert insert.pack_fct(d, {}) == d
    for c in (1, 15):
        o, s = fct.children(d)[c]
        assert insert.pack_fct(d[o:o + s], {}) == d[o:o + s]


@work
def test_font_page_added():
    d = (extract.CPK / "00003.bin").read_bytes()
    o, s = fct.children(d)[1]
    d1 = d[o:o + s]
    k = fct.children(d1)
    pages, info = vwf.fonts(lambda c: d1[k[c][0]:k[c][0] + k[c][1]])
    for fid, f in vwf.FONTS.items():
        new, old = pages[f["child"]], d1[k[f["child"]][0]:k[f["child"]][0] + k[f["child"]][1]]
        if fid == 4:  # one texture, taller, with the old cells untouched
            a, b = ptx.parse(old), ptx.parse(new)
            assert (b["w"], b["h"], b["lh"]) == (120, 336, 9) and info[4][0] == 180
            sb = a["stride"] // 2
            assert ptx.unswizzle(new[b["doff"]:], sb, b["h"])[:sb * a["h"]] == ptx.unswizzle(old[a["doff"]:], sb, a["h"])
            assert all(info[4][1][c] == 12 for c in range(0x30, 0x3A))
            continue
        n = struct.unpack_from("<I", old, 4)[0]
        assert struct.unpack_from("<I", new, 4)[0] == n + 1
        offs = struct.unpack_from(f"<{n + 1}I", new, 0x10)
        assert all(new[x:x + 4] == b"PTX@" and x % 32 == 0 for x in offs)
        assert info[fid][0] > 0 and all(1 <= v <= f["cell"] for v in info[fid][1].values())


@work
def test_eboot_rewrite_layout():
    elf = extract.ELF.read_bytes()
    eb = elfpatch.Eboot(elf, insert.SEG_VADDR)
    eb.append(b"\x11" * 100)
    eb.rels += [(0x9E978, elfpatch.R_26), (insert.SEG_VADDR + 4, elfpatch.R_26)]
    out = eb.serialize()
    shoff, phnum, shnum = struct.unpack_from("<I", out, 32)[0], struct.unpack_from("<H", out, 44)[0], struct.unpack_from("<H", out, 48)[0]
    assert phnum == 2 and shnum == struct.unpack_from("<H", elf, 48)[0]  # same headers as the dump (issue #4)
    assert out[0x34:0x54] + out[0x74:0x2BFD18] == elf[0x34:0x54] + elf[0x74:0x2BFD18]  # program header 0 (p_paddr), segment 0
    ph1 = struct.unpack_from("<8I", out, 0x34 + 32)
    assert ph1[4] == ph1[5] == insert.SEG_VADDR - 0x2BFCA0 + 100
    blob = ph1[1] + insert.SEG_VADDR - 0x2BFCA0
    assert out[ph1[1]:ph1[1] + 0x204] == elf[0x2BFD18:0x2BFF1C] and out[blob:blob + 100] == b"\x11" * 100
    assert insert.SEG_VADDR >= 0x2BFCA0 + 0xA327C  # past segment 1's bss
    rels = []
    for i in range(shnum):
        a = struct.unpack_from("<10I", elf, struct.unpack_from("<I", elf, 32)[0] + i * 40)
        b = struct.unpack_from("<10I", out, shoff + i * 40)
        if a[1] and a[1] != 8:  # every section's bytes are still there
            assert out[b[4]:b[4] + a[5]] == elf[a[4]:a[4] + a[5]], i
        if b[1] == elfpatch.SHT_PSPREL:
            rels.append(out[b[4]:b[4] + b[5]])
    assert rels[-1][-16:] == struct.pack("<4I", 0x9E978, 4, insert.SEG_VADDR + 4 - 0x2BFCA0, 4 | 1 << 8)


def test_marker_keeps_codes():
    s = marker.marker("{voice:002800}あいう{n}えお%dか", "E1.2")
    assert s.startswith("{voice:002800}[E1.2]")
    assert s.count("{n}") == 1 and s.count("%d") == 1
    assert s.index("{n}") < s.index("%d")
    assert extract.TBL.encode(s)
