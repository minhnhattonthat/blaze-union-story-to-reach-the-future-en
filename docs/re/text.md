# Text, scripts and fonts

Disc: ULJM05503, 582,221,824 bytes. `PSP_GAME/USRDIR/Data/Data.cpk` (448 MB) and `Movie/BU_OP.pmf` (opening movie).

## Data.cpk (verified: `tests/test_itoc.py`, full extract asserts every size)

ITOC-only CRI CPK: 3,340 files, numeric IDs, no names, `Align` 2048, files in ID order from `ContentOffset`. 1,467 are
CRILAYLA-compressed, the rest stored. `tools/itoc.py x` extracts to `work/cpk/<id>.<ext>` with `index.tsv`.

The rebuild path is untested: `tools/cpk.py` refuses ITOC-only archives, so phase 3 needs its own repacker, plus a
CRILAYLA encoder or storing edited files uncompressed (guess: the engine honours FileSize == ExtractSize as stored, as
1,873 files here already do).

| IDs | Magic | What | State |
|---|---|---|---|
| 0, 1, 3, 146-161, 1467-1522, 2031-2049 | `FCT\0` | Container: u32 count at +4, u32 table offset at +8, then (u32 offset, u32 size) pairs. `tools/fct.py` | verified on 0, 1, 3, 3/001, 3/015 |
| 2, 4, 1523-1604, 1770-1771, 1824, 1970-2028 ... | `PTP\0` | Texture pack: u32 count at +4, u32 offsets from +0x10 | verified on 3/004 |
| 5-20, 69-110, 162-295, 1605-1712 ... | `PTX@` | Texture, see `graphics.md` | verified |
| 21-68, 111-145, 1044-1096 ... | `PTG@` | Sprite group: cell table plus embedded PTX slices. Cell format not decoded | guess |
| 296-342 ... | `PTA\0` | Animation data plus PTX; some PTX have no palette of their own | guess |
| 343-981 | none | 639 files of big-endian offset/size tables | unknown; no real text found |
| 982-1043, 2642+ | `80 00` | CRI ADX audio | verified by CRI copyright string |
| 1713-1769 | `FPD\0` | 57 files, the same count as the event scripts: per-script picture packs | guess |
| 1826-1969 | `02 1e` | 144 files of 602 bytes | unknown |
| 2050-2065 | PNG | 16 images, 144x80 | verified |
| **2149-2205** | none | **57 event scripts** (below) | verified |
| 2206-2641 | `VPD\0` | 436 packs, large. Guess: voice or portrait data | guess |

Inventory tools: `tools/survey.py`, `tools/textscan.py`, `tools/grepjp.py`.

## Where the text is

| Source | Size | Encoding | Notes |
|---|---|---|---|
| Event scripts 2149-2205 | about 260k Japanese chars (`work/textscan.tsv`) | Shift-JIS | Main story |
| EBOOT `code.bin` 0x1D0000-0x2B0000 | about 8,600 strings, 180 KB total in the EBOOT | Shift-JIS | Battle quips, skills, items, units, menus, chapter log |
| FCT 3 child 15 (11 children, `work/fct/00003_015/`) | about 37k chars | Shift-JIS | Defeat lines, tutorial (008), food and item comments (009) etc. Most start with a u32 offset table; 006 and 007 are bare strings |
| FCT 1 child 0 (`FORM`/`EXIF`, 464 KB) | 76 strings | Shift-JIS | "EXIF" effect data with names such as マントラップ. Format not decoded |

**Prologue scroll and chapter cards are not text.** `帝国西部に位置` and `先帝である` appear in no EBOOT, CPK or FCT child
(`tools/grepjp.py`), so they are images, as is the chapter title card seen in-game (義賊団参上! / ティエラ・ネザー地区西).

## Event script format (file 2149 traced; layout checked on all 57)

- u32[0] == file size - 0x14 (**verified** on all 57). 10 u32 header ends at 0x28; u32[1..9] are bytecode entry points.
- Messages: NUL-terminated strings packed from 0x28. They end where bytecode starts, which is **before** u32[1]
  (2149: messages to about 0x920, u32[1] = 0x9F5). `tools/evscript.py text_entries()` still uses u32[1] and overruns
  into bytecode: fix before extraction.
- Bytecode: `[op u8, len u8, args]`, len includes both, with exceptions: ops 0x52 and 0x53 (`52 02`) are followed by
  an inline table of u32 targets, and data seems to sit between some ops. `walk_ops` stops early in all 57 files, so
  the walk is **incomplete**.
- **Jumps are absolute file offsets**, e.g. `05 06 <u32>`, `10 07 f8 <u32>`, `13 09 .. <u32>`, `07 07 00 <u32>`.
- **A message reference is `46 07 00 <u32 file offset>`** (**verified**: read breakpoint on message 0x28 fired with VM
  IP at file 0xBE5, where `46 07 00 28 00 00 00` sits; in 2149, 43 of the operands equal to a message start belong to
  op 0x46, and a handful of other hits are chance matches).

**Insert plan (guess until phase 5):** leave code in place, append English messages at the end of the file, repoint
each op 0x46 operand. No jump changes. This needs a clean list of 0x46 sites, u32[0] updated, and a test that the longer
file fits the load buffer. Scene 1 loads at RAM 0x08B8A364; the buffer's size is unknown.

## Printer (`vaddr 0x9E8DC`, **verified** by read breakpoints on message bytes; codes read from disassembly)

| Byte | Meaning |
|---|---|
| 00 | End of string, or return if a substring is on the stack (0x94(s3) depth, pointers at 0x88(s3)) |
| 01 | Newline |
| 02 xx lo hi | Voice cue: u16 id (FFFF = none), read 2 bytes after the code; calls 0x10DCB0(id, 0x64). So `02 00 28 00` at a message start is voice 0x28, **not** a record tag |
| 03 nn | Inline substring by u8 index, via a pointer table at [0x8B12C] |
| 04 lo hi | Inline substring by u16 index, same table |
| 05-1F | Below 0x20: falls to the two-byte branch at 0x9EE28. Not seen in real messages so far; confirm at extraction |
| 20-7F, font 0 | **Half-width ASCII, 8x8 cells**: sx = (c-0x20 & 0xF) * 8, sy = (c-0x20 & 0xF0) / 2, sheet pointer at [0x8B128] |
| 20-7F, other fonts | Mapped to a full-width code through the table at 0x27B1C8, with ligatures `!?`, `!!`, `Lv`, `r.`, then a normal glyph lookup |
| 80-FF | Shift-JIS pair, with lookahead at 0x9E8D4 (ligature check, guess), then glyph lookup 0x9E668. Unknown glyph falls back to a fixed cell |

`87 41`, `87 42` (②, ③ in cp932) occur inside dialogue as the game's own emphasis glyphs (611 and 161 times). Identify
them against the font before translating: guess, "!!"-style marks.

Layout: **fixed cell grid.** Each glyph is a 0x24-byte record (col at +0, row at +2, cell w/h at +4/+6, source rect at
+0xC..+0x12), with limits cols 0x18(s3), rows 0x1A(s3). Cell size by font id, table at 0x27B28A: font 0 = 8, 1 = 20,
2 = 18, 3 = 24, 4 = 12. **No VWF.** English needs engine work (phase 5): the record's col is per-glyph, so a pixel-based
advance looks possible; the record buffer's capacity (guess: cols x rows) limits how many glyphs fit.

## Fonts (FCT 3 child 1, `work/fct/00003_001/`)

| Child | Content |
|---|---|
| 000 | PTX 120x216 T4: 12x12 number sheet; font 4 indexes it by value (`%10`, `/10`), no charset |
| 001 + 002 | PTP 504x504, 504x450 T4 + charset of 1,484 codes: 24x24 by sheet width (guess) |
| 003 + 004 | PTP 500x500 x3, 500x380 T4 + charset of 2,334 codes: 20x20 by sheet width (guess) |
| 005 + 006 | PTP 504x504, 504x96 T4 + charset of 508 codes: 18x18 by sheet width (guess) |

Charset file: u32 offset of a bucket table, then u16 Shift-JIS codes, zero-terminated. Bucket boundaries in the EBOOT at
0x27B1AA (0x824F 0x8260 0x829F 0x8340 0x839F 0x889F 0x8DB1 0x93DE 0x9680 0x9785 0x989F, **read from bytes**). Glyph index
= position in the list. The 8x8 ASCII sheet (font 0) has not been located, and which font id dialogue uses is not
confirmed (the 20 in a printer argument is a hint, not proof).

## EBOOT strings and free space

- Strings sit on 4-aligned starts, NUL-terminated, with 0x01 newlines. Pointer tables hold raw vaddrs in segment 0
  (**verified** for 3 strings: ジルヴァ 0x2596E4 at table 0x2ADF24, 武器職人 0x25A0BC at 0x2AE7C4, 巨獣ロコンの骨 0x234D70 at
  0x28C9A0). The relocation table rebases them at load, so repointing inside segment 0 needs no relocation change
  (guess). A string may also be built by `lui`/`addiu` in code: check with `disasm.py xref` before moving it.
- Segment 0: vaddr 0, 2,882,720 bytes, no slack known. Segment 1: vaddr 0x2BFCA0, 516 bytes in file, 668,284 in memory.
  Some `lui` immediates look segment-1-relative: one attempt (0x8B130 + 0x2BFCA0 + 0x8804000) read zeros, so this is
  **unresolved**.
- Free space plan: Japanese takes 2 bytes per char and half-width English about 1, so in-place packing of the 180 KB
  string area plausibly fits (guess, needs counting at phase 6). Overflow: a third segment or a data file, phase 5.
- Files on disc: `iso9660.patch` appends larger files to the image end. The CPK can grow that way. Real-hardware UMD
  limits do not apply to an ISO on memory stick.
- The shipped EBOOT has to be the plain ELF: PPSSPP and CFW accept it, stock firmware does not. Noted under "Waiting
  on the user" in `docs/status.md`.

## Earlier work

- No English patch found. Web search, 2026-11-07.
- lltvg wiki translation project (http://www.lltvg.com/wiki/Blaze_Union/ja-en): a script translation, no patch, about
  1% done when announced on Lacrima Castle. Not read.
- Altiari's GameFAQs/Neoseeker walkthrough uses non-standard names (Siscia); not a name source.
- datacrystal.tcrf.net has a Blaze Union page. **Not read**: tcrf.net is denied by the skill's rule. Everything here was
  worked out from the dump.
- Names: Yggdra Union (Atlus USA) is the official source for Gulcasa, Nessiah, Emilia, Aegina, Baldus, Leon, Russell,
  Pamela, Zilva, Eudy, Inzaghi (spelling to check), Milanor, Yggdra. Blaze-only names (Garlot, Siskier, Jenon, Medoute)
  come from English Wikipedia and an artbook translation: no official English source exists. Build the table at phase 6.

## Open items for later phases

1. Complete bytecode walk (op 0x52/0x53 tables, data gaps), so the 0x46 list is provably complete.
2. Which font id dialogue, speaker names and menus use. Location of the 8x8 sheet.
3. Script load buffer size. Record-buffer capacity in the printer.
4. Speaker name source (恰幅のいい商人 on the first dialogue): the EBOOT unit table, drawn with a large italic face.
