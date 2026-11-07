"""Variable-width English on the game's fixed-cell printer (docs/re/text.md, Printer).
- Font: ASCII glyphs go on an extra page of each sheet (FCT 3/1 children 1, 3, 5); width table per font.
- Hooks: each window gets K times the glyph slots, a record's +0 holds its pixel x instead of a column, and the printer keeps
  a pen at 0x4C(sp) (an unused word of its frame). The advance of the last glyph lives in the record's high flag byte (+0x1F),
  so the typewriter, which returns after each glyph, can pick the pen up again."""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import mips
import ptx
from elfpatch import R_26

ROOT = Path(__file__).resolve().parents[1]
TTF = ROOT / "fonts/SourceSans3-Semibold.ttf"
K = 4  # glyph slots per original cell: a 20 px cell then holds four glyphs of 5 px average, more than English needs
FONTS = {1: dict(child=3, cell=20, size=16), 2: dict(child=1, cell=18, size=15), 3: dict(child=5, cell=24, size=20),
         4: dict(child=0, cell=12, size=11)}  # 4: the 12 px pixel font, one PTX and no charset; its palette is clear, white, black
FIRST, LAST = 0x20, 0x7E
GLYPHS = 0x60  # 0x20..0x7F
SPACE = 5  # px, by eye: the TTF's own space looks thin next to the outline
ARENA_GROW = 0x80000
# Item text, no {n}, the two screens wrap it differently: string pointers, their end, break table, breaks per string, font, line px
WRAPS = ((0x28C040, 0x28C494, 0x289C78, 1, 1, 250), (0x28C494, 0x28C8E8, 0x2B7FA8, 2, 2, 140))


def render(size, cell, fid=1):
    """-> (indexed glyph rows per char, widths). Index 0 clear, 1 black outline, 2-14 grey to white, as the Japanese glyphs.
    Font 4 is two colours: 0 clear, 1 white, 2 black outline, drawn without smoothing.
    Font 2 is dark ink on the extras' paper, no outline: 1 darkest to 14 lightest; page() turns 0 into its clear index, 15."""
    font = ImageFont.truetype(str(TTF), size)
    asc, desc = font.getmetrics()
    base = (cell + asc - desc) // 2 - 1
    ink, edge = (1, 2) if fid == 4 else (None, 1)
    dark = fid == 2
    glyphs, widths = {}, {}
    for c in range(FIRST, LAST + 1):
        ch = chr(c)
        adv = round(font.getlength(ch))
        im = Image.new("L", (cell + 4, cell), 0)
        draw = ImageDraw.Draw(im)
        if ink:
            draw.fontmode = "1"
        draw.text((1, base), ch, 255, font=font, anchor="ls")
        px = im.load()
        out = [[0] * cell for _ in range(cell)]
        for y in range(cell):
            for x in range(cell):
                v = px[x, y]
                if v >= 24:
                    out[y][x] = 1 + ((255 - v) * 13) // 255 if dark else ink or 2 + (v * 12) // 255
        for y in range(cell):  # outline: the 8 neighbours of ink, as black
            for x in range(cell):
                if not dark and out[y][x] == 0 and any(out[j][i] not in (0, edge) for j in range(max(0, y - 1), min(cell, y + 2))
                                          for i in range(max(0, x - 1), min(cell, x + 2))):
                    out[y][x] = edge
        glyphs[c] = out
        widths[c] = SPACE if ch == " " else min(max(adv, 1) + 1, cell)
        if fid == 4 and ch.isdigit():  # keeps the game's own digit cells
            widths[c] = cell
    return glyphs, widths


def swizzle(rows, sb):
    """Inverse of ptx.unswizzle, 16-byte x 8-row blocks."""
    out = bytearray()
    for by in range(0, len(rows) // sb, 8):
        for bx in range(0, sb, 16):
            for y in range(8):
                p = (by + y) * sb + bx
                out += rows[p:p + 16].ljust(16, b"\0")
    return bytes(out)


def page(d, offs, cols, cell, glyphs, clear=0):
    """A new PTX in the format of the sheet's last page, holding GLYPHS cells. `clear`: the sheet's transparent index."""
    last = ptx.parse(d, offs[-1])
    rows_n = (GLYPHS + cols - 1) // cols
    h = rows_n * cell
    sb = last["stride"] // 2
    rows = bytearray(bytes([clear * 0x11]) * (sb * ((h + 7) // 8 * 8)))
    for c, g in glyphs.items():
        i = c - FIRST
        x0, y0 = (i % cols) * cell, (i // cols) * cell
        for y, r in enumerate(g):
            for x, v in enumerate(r):
                if v:
                    X = x0 + x
                    p = (y0 + y) * sb + X // 2
                    rows[p] = rows[p] & 0x0F | v << 4 if X & 1 else rows[p] & 0xF0 | v
    head = bytearray(d[offs[-1]:offs[-1] + last["doff"]])  # header and palette
    head[8:10] = struct.pack("<H", last["w"])
    head[10:12] = struct.pack("<H", h)
    return bytes(head) + swizzle(bytes(rows), sb)


def add_page(d, cell, cols, glyphs, clear=0):
    """PTP with one more page. The offset table grows at +0x10, so pages shift when it would reach the first page."""
    assert d[:4] == b"PTP\0", d[:4]
    n = struct.unpack_from("<I", d, 4)[0]
    offs = list(struct.unpack_from(f"<{n}I", d, 0x10))
    new = page(d, offs, cols, cell, glyphs, clear)
    shift = 0 if 0x10 + (n + 1) * 4 <= offs[0] else 0x40 - offs[0] if offs[0] < 0x40 else 0x40
    body = d[offs[0]:]
    body += bytes(-(offs[0] + shift + len(body)) % 64)  # pages are 64-aligned
    head = bytearray(d[:offs[0]]) + bytes(shift)
    offs = [o + shift for o in offs]
    offs.append(offs[0] + len(body))
    struct.pack_into("<I", head, 4, n + 1)
    struct.pack_into(f"<{n + 1}I", head, 0x10, *offs)
    return bytes(head) + body + new


def grow_sheet(d, cell, glyphs):
    """Font 4's single PTX with the English cells added below its rows. -> (new bytes, first glyph index)."""
    h = ptx.parse(d)
    sb, cols = h["stride"] // 2, h["w"] // cell
    assert h["fmt"] == 4 and h["h"] % 8 == 0 and h["doff"] + sb * h["h"] == len(d)
    rows = bytearray(ptx.unswizzle(d[h["doff"]:], sb, h["h"]))
    new_h = h["h"] + (GLYPHS + cols - 1) // cols * cell
    assert new_h % 8 == 0
    rows += bytes(sb * (new_h - h["h"]))
    first = h["h"] // cell * cols
    for c, g in glyphs.items():
        i = first + c - FIRST
        x0, y0 = (i % cols) * cell, (i // cols) * cell
        for y, r in enumerate(g):
            for x, v in enumerate(r):
                if v:
                    X = x0 + x
                    rows[(y0 + y) * sb + X // 2] |= v << 4 if X & 1 else v
    head = bytearray(d[:h["doff"]])
    head[5] = max(head[5], (new_h - 1).bit_length())
    head[10:12] = struct.pack("<H", new_h)
    return bytes(head) + swizzle(bytes(rows), sb), first


def fonts(children):
    """{FCT 3/1 child: new bytes}, {font id: (first glyph index, widths by char)}. `children` reads a child by number."""
    out, info = {}, {}
    for fid, f in FONTS.items():
        d = children(f["child"])
        glyphs, widths = render(f["size"], f["cell"], fid)
        if fid == 4:
            out[f["child"]], first = grow_sheet(d, f["cell"], glyphs)
            info[fid] = (first, widths)
            continue
        charset = children(f["child"] + 1)
        cols, _, cw, ch, per = struct.unpack_from("<5I", charset, struct.unpack_from("<I", charset)[0])
        assert cw == ch == f["cell"], (cw, f)
        n = struct.unpack_from("<I", d, 4)[0]
        out[f["child"]] = add_page(d, f["cell"], cols, glyphs, 15 if fid == 2 else 0)
        info[fid] = (per * n, widths)
    return out, info


ROUTINES = """
# 9e978: lw s2, 0x14(s3) replaced; a0 and t1 and v0 stay live.  v0 != 0: typewriter, s5 is already a slot number
enter:
    lw $s2, 0x14($s3)
    bnez $v0, enter_tw
    nop
    move $t8, $ra
    bal enter_0
    nop
enter_0:
    addu $t9, $ra, $s4          # cell table indexed by font
    lbu $t9, CELLS-enter_0($t9)
    move $ra, $t8
    lh $t8, 8($s3)
    addu $t9, $t9, $t8
    mult $s5, $t9
    mflo $t8
    sw $t8, 0x4C($sp)
    jr $ra
    sll $s5, $s5, 2             # K = 4
enter_tw:
    beqz $s5, enter_tw0
    move $t8, $zero
    lh $t8, 0x18($s3)
    mult $t8, $fp
    mflo $t8
    addu $t8, $t8, $s5
    addiu $t8, $t8, -1
    sll $t9, $t8, 5
    sll $t8, $t8, 2
    addu $t8, $t8, $t9
    addu $t8, $t8, $s2          # previous record
    lh $t9, 0($t8)
    lbu $t8, 0x1F($t8)
    addu $t8, $t8, $t9
enter_tw0:
    jr $ra
    sw $t8, 0x4C($sp)

# 9ec34: sh s5, 0(s2) replaced: a record holds pixels, not its column
store:
    lw $a0, 0x4C($sp)
    jr $ra
    sh $a0, 0($s2)

# 9eae8: newline resets the pen
newline:
    sw $zero, 0x4C($sp)
    lw $a0, 0x10($sp)
    jr $ra
    nop

# 9ec78: or a0,a0,a1 in the delay slot; sw and slti moved here. a2 = first byte of the character
advance:
    sw $a0, 0x34($s3)
    move $t8, $ra
    lh $t7, 0x1C($s3)           # cell + spacing, the original advance
    lh $t9, 8($s3)
    addu $t7, $t7, $t9
    addiu $t9, $s4, -1
    sltiu $t9, $t9, 4
    beqz $t9, advance_1
    addiu $t6, $a2, -0x20
    sltiu $t9, $t6, 0x60
    beqz $t9, advance_1
    addiu $t9, $s4, -1
    sll $t5, $t9, 6
    sll $t9, $t9, 5
    addu $t9, $t9, $t5
    addu $t9, $t9, $t6          # (font - 1) * 96 + char
    bal advance_0
    nop
advance_0:
    addu $t9, $ra, $t9
    lbu $t7, WIDTHS-advance_0($t9)
advance_1:
    lw $t9, 0x4C($sp)
    addu $t9, $t9, $t7
    sw $t9, 0x4C($sp)
    bnez $s7, advance_2
    nop
    sb $t7, 0x1F($s2)
advance_2:
    move $ra, $t8
    jr $ra
    slti $a0, $a2, 0x20

# a0324 and a052c, top of the row loop of the two lay-out calls: some callers lay a string out cell by cell at
# x = start + i * cell. If the slot before this run holds a laid-out glyph, go on from its end instead of the given x.
# a0 = cols. In a0248: t7 col offset, v1 row, a3 window, t3 x. In a0428: t8 col offset, t0 row, a2 window, t1 x
layout_a:
    mult $a0, $v1
    mflo $a1
    sll $v0, $a1, 5
    sll $a1, $a1, 2
    addu $a1, $a1, $v0
    beqz $t7, layout_a_1
    addu $a1, $a1, $t7
    lw $v0, 0x14($a3)
    addu $a1, $a1, $v0
    lw $v0, -0x1C($a1)
    srl $v0, $v0, 24
    beqz $v0, layout_a_1
    lhu $v0, -6($a1)
    andi $v0, $v0, 1
    beqz $v0, layout_a_1
    lh $v0, -0x24($a1)
    lbu $a1, -5($a1)
    addu $t3, $v0, $a1
layout_a_1:
    jr $ra
    mult $a0, $v1
layout_b:
    mult $a0, $t0
    mflo $a1
    sll $v0, $a1, 5
    sll $a1, $a1, 2
    addu $a1, $a1, $v0
    beqz $t8, layout_b_1
    addu $a1, $a1, $t8
    lw $v0, 0x14($a2)
    addu $a1, $a1, $v0
    lw $v0, -0x1C($a1)
    srl $v0, $v0, 24
    beqz $v0, layout_b_1
    lhu $v0, -6($a1)
    andi $v0, $v0, 1
    beqz $v0, layout_b_1
    lh $v0, -0x24($a1)
    lbu $a1, -5($a1)
    addu $t1, $v0, $a1
layout_b_1:
    jr $ra
    mult $a0, $t0

# Item text is one printed row that the game laid out cell by cell, breaking lines after counts from a table. Now by glyph, not cell.
# a0 window, a1 x, a2 y, a3 first break, t0 second break (0 none), t1 line height; slot numbers. Row 0 holds the text
wrap:
    lw $t2, 0x14($a0)
    move $t3, $a1
    move $t4, $zero
wrap_1:
    lbu $t5, 0x1F($t2)
    beqz $t5, wrap_3
    nop
    sh $t3, 0($t2)
    sh $a2, 2($t2)
    lhu $t6, 0x1E($t2)
    ori $t6, $t6, 1
    sh $t6, 0x1E($t2)
    addu $t3, $t3, $t5
    addiu $t4, $t4, 1
    beq $t4, $a3, wrap_2
    addiu $t2, $t2, 0x24
    bne $t4, $t0, wrap_1
    nop
wrap_2:
    move $t3, $a1
    addu $a2, $a2, $t1
    beq $zero, $zero, wrap_1
    nop
wrap_3:
    lw $t5, 0x34($a0)
    lui $t6, 0x800
    or $t5, $t5, $t6
    jr $ra
    sw $t5, 0x34($a0)

# 120778: the book's item page. s5 -> item id, s4 break table, s3 first break, s1 x, s7 x offset, s2 y
wrap_item:
    lhu $t0, 0($s5)
    addu $t0, $t0, $t0
    addu $t0, $t0, $s4
    lbu $t0, 1($t0)
    lw $a0, 0x8C($s6)
    addu $a1, $s1, $s7
    move $a2, $s2
    move $a3, $s3
    beq $zero, $zero, wrap
    ori $t1, $zero, 15

# d557c and d5714: the item line of the equip screen, two copies. a0 is the window already
wrap_card_a:
    ori $a1, $zero, 0x18
    move $a2, $s1
    addiu $a3, $s2, 1
    move $t0, $zero
    beq $zero, $zero, wrap
    ori $t1, $zero, 0x14
wrap_card_b:
    ori $a1, $zero, 0x18
    move $a2, $s4
    addiu $a3, $s1, 1
    move $t0, $zero
    beq $zero, $zero, wrap
    ori $t1, $zero, 0x14

# 9ecf8: bne a2, a3 replaced. Fonts 1-4: our page, no ligatures, on to the draw at 9edfc. Else the original tests.
# Font 4's digits stay the game's own: stats and counters print through it
ascii:
    addiu $t9, $s4, -1
    sltiu $t9, $t9, 4
    beqz $t9, ascii_1
    move $t8, $ra
    addiu $t9, $s4, -4
    bnez $t9, ascii_3
    addiu $t9, $a2, -0x30
    sltiu $t9, $t9, 10
    bnez $t9, ascii_1
    nop
ascii_3:
    bal ascii_0
    nop
ascii_0:
    sll $t9, $s4, 1
    addu $t9, $ra, $t9
    lhu $a1, BASES-ascii_0($t9)
    addiu $t9, $a2, -0x20
    addu $a1, $a1, $t9
    addiu $ra, $t8, 0xFC
    jr $ra
    nop
ascii_1:
    beq $a2, $a3, ascii_2
    nop
    addiu $ra, $ra, 0x2C
ascii_2:
    jr $ra
    nop
"""


def install(eb, info):
    """Write the hook code and tables into the new segment and patch the printer, the window allocator and the draw."""
    cells = bytes([8, 20, 18, 24, 12, 0, 0, 0])
    bases = b"".join(struct.pack("<H", info[f][0] if f in info else 0) for f in range(5))
    widths = b"".join(bytes(info[f][1].get(c, 0) for c in range(0x20, 0x80)) for f in (1, 2, 3, 4))
    base = eb.append(b"", 16)
    data = bytearray()
    # first pass finds the code size, the tables follow it; the offsets stand in as labels' arithmetic
    src = ROUTINES
    code, labels = mips.asm(src.replace("CELLS-enter_0", "0").replace("WIDTHS-advance_0", "0").replace("BASES-ascii_0", "0"), base)
    table = base + len(code)
    cells_at, bases_at, widths_at = table, table + len(cells), table + len(cells) + len(bases)
    src = (src.replace("CELLS-enter_0", str(cells_at - labels["enter_0"]))
              .replace("WIDTHS-advance_0", str(widths_at - labels["advance_0"]))
              .replace("BASES-ascii_0", str(bases_at - labels["ascii_0"])))
    code, labels = mips.asm(src, base)
    data += code + cells + bases + widths
    eb.append(bytes(data))

    def jal(name):
        return 3 << 26 | labels[name] >> 2

    nop = 0
    eb.hook(0x9E978, 0x8E720014, jal("enter"), R_26)
    eb.hook(0x9EC34, 0xA6550000, jal("store"), R_26)
    eb.hook(0x9EAE8, 0x0004F400, jal("newline"), R_26)
    eb.hook(0x9EAEC, 0x8FA40010, 0x0004F400)  # delay slot: the sll that sat at 9eae8
    eb.hook(0x9EC78, 0x00852025, jal("advance"), R_26)
    eb.hook(0x9EC7C, 0xAE640034, 0x00852025)  # delay slot: the or that sat at 9ec78
    eb.hook(0x9EC80, 0x28C40020, nop)  # slti now in advance
    eb.hook(0x9ECF8, 0x14C7000C, jal("ascii"), R_26)
    eb.hook(0x9F860, 0x00C73021, 0x34060001)  # draw: x = record x * 1, not column * (cell + spacing)
    eb.hook(0xA0140, 0x00059400, 0x00059480)  # window allocator: cols * K, by shifting 2 more before the sign extend
    # cell-range calls (lay out, colour, hide, show, clear) take col and ncols in cells: scale them like the printer's col
    for site in (0xA025C, 0xA0268, 0xA043C, 0xA0454, 0xA064C, 0xA065C, 0xA079C, 0xA089C, 0xA0A00, 0xA0A04):
        w = eb.word(site)
        assert w & 0xFC00003F == 0 and w >> 6 & 31 == 16, hex(site)  # sll x, y, 16
        eb.hook(site, w, w + (2 << 6))
    # lay-out calls place glyphs at absolute x: step by the glyph's advance, not the cell width, and drop the cell spacing
    one = lambda s: int.from_bytes(mips.asm(s)[0], "little")
    eb.hook(0xA0384, one("lh $a1, 4($s0)"), one("lbu $a1, 0x1F($s0)"))
    eb.hook(0xA058C, one("lh $a1, 4($s1)"), one("lbu $a1, 0x1F($s1)"))
    eb.hook(0xA0594, one("addu $a1, $a1, $t4"), one("addu $a1, $a1, $zero"))
    for site, win, reg, name in ((0xA0324, "a3", "v1", "layout_a"), (0xA052C, "a2", "t0", "layout_b")):
        eb.hook(site, one(f"lh $a0, 0x18(${win})"), jal(name), R_26)
        eb.hook(site + 4, one(f"mult $a0, ${reg}"), one(f"lh $a0, 0x18(${win})"))
    eb.hook(0x1161B8, one("ori $a0, $zero, 0xfc"), one("ori $a0, $zero, 0xbe"))  # game over text: x=190, so a line of defeat text gets 288 px
    # 12f124, the win condition panel, lays its strings out itself: of ASCII it knows only 'o' (+10) and 'r' (+14), other bytes get
    # no position and stay hidden. Every ASCII byte now takes the 'o' path with the glyph's advance; the loop covers all K * 30 slots
    eb.hook(0x12F464, one("ori $a2, $zero, 0x6f"), one("lbu $a2, 0x1F($s0)"))
    eb.hook(0x12F468, 0x14860000 | (0x12F494 - 0x12F46C) >> 2, nop)
    eb.hook(0x12F46C, one("ori $a2, $zero, 0x72"), nop)
    eb.hook(0x12F474, one("addiu $a0, $s4, 0xa"), one("addu $a0, $s4, $a2"))
    eb.hook(0x12F4F8, one("slti $a0, $s1, 0x1e"), one(f"slti $a0, $s1, {0x1E * K}"))
    # item text: the cell-by-cell loops become a call to wrap, then a branch past the loop
    for site, expect, name, past in ((0x120778, one("andi $a1, $s0, 0xff"), "wrap_item", 0x120814),
                                     (0xD557C, one("andi $a1, $s3, 0xff"), "wrap_card_a", 0xD55E0),
                                     (0xD5714, one("andi $a1, $s2, 0xff"), "wrap_card_b", 0xD5778)):
        eb.hook(site, expect, jal(name), R_26)
        eb.hook(site + 4, eb.word(site + 4), nop)
        eb.hook(site + 8, eb.word(site + 8), 0x10000000 | (past - (site + 12)) >> 2)
        eb.hook(site + 12, eb.word(site + 12), nop)
    # heap: arena 0 holds FCT 3 (5.56 MB of 5.77 MB) and the loads after it; grow it and the total by ARENA_GROW
    eb.hook(0xEFC08, 0x3C050134, 0x3C050134 + (ARENA_GROW >> 16))
    eb.hook(0xEFC4C, 0x3C120058, 0x3C120058 + (ARENA_GROW >> 16))
    return labels


def breaks(s, n, font, px, table=None):
    """Word wrap: n bytes for a break table, the glyph count before each break. Text past the last break runs on: the lint's to catch."""
    w = table or widths()[font]
    out, x, start, last = [], 0, 0, None
    for i, c in enumerate(s):
        x += w[ord(c)]
        if c == " ":
            last = i + 1
        if x > px and last and len(out) < n:
            out.append(last)
            x = sum(w[ord(k)] for k in s[last:i + 1])
            start, last = last, None
    return bytes(out + [0] * (n - len(out)))


def widths():
    """{font id: {char: px}} for the lint and the marker text."""
    return {fid: render(f["size"], f["cell"], fid)[1] for fid, f in FONTS.items()}
