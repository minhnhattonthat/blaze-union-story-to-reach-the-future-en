"""Card Select: the card's effect and use condition drawn with the game's font, as Card Data does and Yggdra Union does on this
screen, instead of the picture strips 2684@3710, @e4b0 (effect) and @37b60 (condition). The English is those strips' rows in
data/gfx.tsv, one line each, picked per card the way the game picks the strip (table()). The EBOOT skill text (0x279C8C) is
Card Data's two-line wording and too wide for this one-line panel. docs/re/cardsel.md has the trace.

One printer window (rows 0-1 effect, rows 2-3 condition), created next to Card Select's own window and freed with it. A string
that spills into its second row is laid out on one line: row 1 follows row 0 after a space."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import extract
import fit
import mips
from elfpatch import R_26, SEG0

FONT = 1  # Card Data's: 20 px cells, VWF page
COLS, ROWS = 15, 4  # cells; the printer gives each cell K = 4 glyph slots
EX, EY = 0x15, 0xD3  # effect line: the strip sat at x 21, y 212 (15 px); a font 1 cell's ink starts 2 px down
CX, CY = 0x59, 0xE3  # condition: the strip sat at x 89, y 229
GAP = 5  # px between the two lines of a string, the font's space
COND_ABGR = 0xFF6868FF  # condition tint, a light red: the glyph fill is white, so this is its colour
CARDS = 39  # the strips' effect rows: 20 in 2684@3710, 19 in @e4b0
EFF_PX, COND_PX = 280, 211  # panel room from x 21 and x 89 to its slanted right edge (about x 305 and 302 at the glyph feet)
RECTS = 0x2898DA  # per card x, y, w, h of its condition in 2684@37b60: 14 px rows, the second column at x 203
GFX = extract.ROOT / "data/gfx.tsv"

ROUTINES = f"""
# v1 -> this module's data (win, last card). Leaves ra in t9 for the return
data:
    move $t9, $ra
    bal data_0
    nop
data_0:
    addiu $v1, $ra, DATA-data_0
    jr $t9
    nop

# d3204, after Card Select made its window: addiu a2, zero, -5 replaced. a1 and a3 stay live
init:
    addiu $sp, $sp, -0x20
    sw $ra, 0x10($sp)
    sw $a1, 0x14($sp)
    sw $a3, 0x18($sp)
    move $a0, $zero
    move $a1, $zero
    ori $a2, $zero, {COLS}
    ori $a3, $zero, {ROWS}
    ori $t0, $zero, 0x3f
    ori $t1, $zero, {FONT}
    move $t2, $zero
    jal 0x9e490
    move $t3, $zero
    sw $v0, 0x1c($sp)
    beqz $v0, init_9
    move $a0, $v0
    ori $a1, $zero, {COLS}
    jal 0xa0130
    ori $a2, $zero, {ROWS}
    lw $a0, 0x1c($sp)
    lw $t0, 0x34($a0)
    addiu $t1, $zero, -7        # bits 4 and 2 clear: hidden until a card is under the cursor
    and $t0, $t0, $t1
    sw $t0, 0x34($a0)
init_9:
    jal data
    nop
    lw $t0, 0x1c($sp)
    sw $t0, 0($v1)
    addiu $t0, $zero, -1
    sw $t0, 4($v1)
    lw $ra, 0x10($sp)
    lw $a1, 0x14($sp)
    lw $a3, 0x18($sp)
    addiu $a2, $zero, -5
    jr $ra
    addiu $sp, $sp, 0x20

# d02d4, after Card Select freed its window: addiu a1, zero, -3 replaced; the delay slot's and a1, a3, a1 is redone. a2, a3 live
free:
    addiu $sp, $sp, -0x20
    sw $ra, 0x10($sp)
    sw $a2, 0x14($sp)
    sw $a3, 0x18($sp)
    jal data
    nop
    lw $a0, 0($v1)
    beqz $a0, free_9
    sw $zero, 0($v1)
    jal 0x9e56c
    nop
free_9:
    lw $ra, 0x10($sp)
    lw $a2, 0x14($sp)
    lw $a3, 0x18($sp)
    addiu $a1, $zero, -3
    and $a1, $a3, $a1
    jr $ra
    addiu $sp, $sp, 0x20

# Window flags +0x34: bit 2 set = drawn (Card Select's own window reads 3 while shown).
# d2438, Card Select's hide (clears bit 2 of its window), reached by j; the delay slot left a1 = -3. Leaf: a1-a3, t0 change
hide:
    lw $a2, 0x4f0($a0)
    beqz $a2, hide_1
    nop
    lw $t0, 0x34($a2)
    and $t0, $t0, $a1
    sw $t0, 0x34($a2)
hide_1:
    move $a2, $ra
    bal hide_2
    nop
hide_2:
    lw $a3, DATA-hide_2($ra)
    move $ra, $a2
    beqz $a3, hide_3
    nop
    lw $t0, 0x34($a3)
    and $t0, $t0, $a1
    sw $t0, 0x34($a3)
hide_3:
    jr $ra
    nop

# d1f94, each frame before the panel: lbu a1, 0(s1) replaced (a0 stays live). Hide ours; text shows it again on a card slot
pre:
    move $t8, $ra
    bal pre_0
    nop
pre_0:
    lw $a1, DATA-pre_0($ra)
    move $ra, $t8
    beqz $a1, pre_1
    nop
    lw $t8, 0x34($a1)
    addiu $t9, $zero, -3
    and $t8, $t8, $t9
    sw $t8, 0x34($a1)
pre_1:
    jr $ra
    lbu $a1, 0($s1)

# d201c, the condition strip's draw: lhu a0, 6(s1) replaced, returns past the draw to d2070. s1 -> slot, +6 card number
text:
    addiu $sp, $sp, -0x30
    sw $ra, 0x10($sp)
    sw $s0, 0x14($sp)
    sw $s1, 0x18($sp)
    sw $s2, 0x1c($sp)
    lhu $s1, 6($s1)
    jal data
    nop
    move $s2, $v1
    lw $s0, 0($s2)
    beqz $s0, text_9
    nop
    lw $t0, 4($s2)
    beq $t0, $s1, text_8
    nop
    sw $s1, 4($s2)
    jal 0xa09a0
    move $a0, $s0
    sltiu $t0, $s1, {CARDS}     # past the table: an empty window
    beqz $t0, text_2
    sll $t0, $s1, 2
    addu $t0, $t0, $s2
    lhu $t1, 8($t0)             # DATA + 8: per card the effect's and the condition's offsets from DATA
    addu $t1, $t1, $s2
    move $a0, $s0
    move $a1, $zero
    move $a2, $zero
    addiu $a3, $zero, -1
    ori $t0, $zero, {FONT}
    move $t2, $zero
    move $t3, $zero
    jal 0x9e8dc
    sw $zero, 0($sp)
    sll $t0, $s1, 2
    addu $t0, $t0, $s2
    lhu $t1, 10($t0)
    addu $t1, $t1, $s2
    move $a0, $s0
    move $a1, $zero
    ori $a2, $zero, 2
    addiu $a3, $zero, -1
    ori $t0, $zero, {FONT}
    move $t2, $zero
    move $t3, $zero
    jal 0x9e8dc
    sw $zero, 0($sp)
    move $a0, $s0               # the strip's condition was red: tint rows 2-3 (ABGR), the outline stays black
    move $a1, $zero
    ori $a2, $zero, 2
    ori $a3, $zero, {COLS}
    ori $t0, $zero, 2
    lui $t1, {COND_ABGR >> 16:#x}
    ori $t1, $t1, {COND_ABGR & 0xFFFF:#x}
    jal 0xa0644
    move $t2, $zero
text_2:
    move $a0, $s0
    ori $a1, $zero, {EX}
    ori $a2, $zero, {EY}
    jal flow
    move $a3, $zero
    move $a0, $s0
    ori $a1, $zero, {CX}
    ori $a2, $zero, {CY}
    jal flow
    ori $a3, $zero, 2
text_8:
    lw $t0, 0x34($s0)
    ori $t0, $t0, 2
    sw $t0, 0x34($s0)
text_9:
    lw $ra, 0x10($sp)
    lw $s0, 0x14($sp)
    lw $s1, 0x18($sp)
    lw $s2, 0x1c($sp)
    addiu $ra, $ra, 0x4c
    jr $ra
    addiu $sp, $sp, 0x30

# d20e0, the effect strip's draw: lhu a0, 6(s1) replaced; past both draws to the epilogue at d21e0
skip:
    addiu $ra, $ra, 0xf8
    jr $ra
    nop

# a0 window, a1 x, a2 y, a3 first row: rows a3 and a3 + 1 on one line, as vwf.wrap places a row (records of 0x24 bytes, +0 x,
# +2 y, +0x1E bit 0 shown, +0x1F advance, 0 past the text)
flow:
    lw $t2, 0x14($a0)
    lh $t3, 0x18($a0)
    sll $t4, $t3, 2
    sll $t5, $t3, 5
    addu $t4, $t4, $t5
    mult $t4, $a3
    mflo $t5
    addu $t2, $t2, $t5
    ori $t6, $zero, 2
flow_r:
    move $t7, $t2
    move $t8, $zero
    move $t9, $zero
flow_g:
    lbu $t5, 0x1F($t7)
    beqz $t5, flow_e
    nop
    sh $a1, 0($t7)
    sh $a2, 2($t7)
    lhu $v0, 0x1E($t7)
    ori $v0, $v0, 1
    sh $v0, 0x1E($t7)
    addu $a1, $a1, $t5
    addiu $t9, $t9, 1
    addiu $t8, $t8, 1
    bne $t8, $t3, flow_g
    addiu $t7, $t7, 0x24
flow_e:
    beqz $t9, flow_n
    nop
    addiu $a1, $a1, {GAP}
flow_n:
    addu $t2, $t2, $t4
    addiu $t6, $t6, -1
    bnez $t6, flow_r
    nop
    lw $t5, 0x34($a0)
    lui $t6, 0x800
    or $t5, $t5, $t6
    jr $ra
    sw $t5, 0x34($a0)
DATA:
"""


def table(elf):
    """-> [(effect, condition)] per card: the English of the strips the original draws. 0xD20E8: the effect is row card of
    2684@3710 under card 20, else row card - 20 of @e4b0; 0xD2028: the condition is the rect at RECTS + card * 8."""
    rows = [r.split("\t") for r in GFX.read_text(encoding="utf-8").splitlines()]
    strip = lambda label: [(int(r[1].split(",")[0]), r[4]) for r in rows if r[0] == label and r[2] == "strip"]
    eff = [s for _, s in strip("2684@3710") + strip("2684@e4b0")]
    cond = strip("2684@37b60")
    cols = [[s for x, s in cond if x == 0], [s for x, s in cond if x]]
    assert len(eff) == CARDS, len(eff)
    out = []
    for c, e in enumerate(eff):
        x, y = struct.unpack_from("<2h", elf, SEG0 + RECTS + c * 8)
        k = cols[x != 0][y // 14]
        assert fit.width(e) <= EFF_PX and fit.width(k) <= COND_PX, f"card {c}: too wide for Card Select: {e!r} / {k!r}"
        out.append((e, k))
    return out


def data(pairs):
    """DATA: window, last card, then per card two u16 offsets from DATA (effect, condition), then the strings."""
    head, strs = bytearray(bytes(8)), bytearray()
    for pair in pairs:
        for s in pair:
            head += struct.pack("<H", 8 + 4 * len(pairs) + len(strs))
            strs += extract.TBL.encode(s) + b"\0"
    return bytes(head + strs)


def assemble(base):
    """-> (code + 8 bytes of data, labels). DATA-label offsets are filled in on a second pass."""
    first = ROUTINES
    for lab in ("data_0", "hide_2", "pre_0"):
        first = first.replace(f"DATA-{lab}", "0")
    _, labels = mips.asm(first, base)
    src = ROUTINES
    for lab in ("data_0", "hide_2", "pre_0"):
        src = src.replace(f"DATA-{lab}", str(labels["DATA"] - labels[lab]))
    code, labels = mips.asm(src, base)
    assert labels["DATA"] == base + len(code)
    return code + bytes(8), labels


def install(eb):
    base = eb.append(b"", 16)
    code, labels = assemble(base)
    assert eb.append(code[:-8] + data(table(eb.elf))) == base
    for i in range(0, len(code) - 8, 4):  # every jal in the new code is absolute: relocate it like the module's own
        if int.from_bytes(code[i:i + 4], "little") >> 26 == 3:
            eb.rels.append((base + i, R_26))
    one = lambda s: int.from_bytes(mips.asm(s)[0], "little")
    jal = lambda n: 3 << 26 | labels[n] >> 2
    j = lambda n: 2 << 26 | labels[n] >> 2
    eb.hook(0xD3204, one("addiu $a2, $zero, -5"), jal("init"), R_26)
    eb.hook(0xD02D4, one("addiu $a1, $zero, -3"), jal("free"), R_26)
    eb.hook(0xD2438, one("ori $a3, $zero, 0"), j("hide"), R_26)
    eb.hook(0xD1F94, one("lbu $a1, 0($s1)"), jal("pre"), R_26)
    eb.hook(0xD201C, one("lhu $a0, 6($s1)"), jal("text"), R_26)
    eb.hook(0xD20E0, one("lhu $a0, 6($s1)"), jal("skip"), R_26)
    return labels


def _selftest():
    code, labels = assemble(0x400000)
    assert len(code) % 4 == 0 and labels["DATA"] == 0x400000 + len(code) - 8
    pairs = table(extract.ELF.read_bytes())
    assert pairs[6] == ("Steals enemy's equipped item", "Siskier only") and pairs[25][1] == "Ace Types must match", pairs
    d = data(pairs)
    assert d[struct.unpack_from("<H", d, 8 + 4 * 6)[0]:].startswith(extract.TBL.encode(pairs[6][0]) + b"\0")
    print("cardsel selftest ok")


if __name__ == "__main__":
    _selftest()
