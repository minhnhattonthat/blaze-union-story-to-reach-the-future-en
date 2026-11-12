# Text, scripts and fonts

Disc: ULJM05503, 582,221,824 bytes. `PSP_GAME/USRDIR/Data/Data.cpk` (448 MB) and `Movie/BU_OP.pmf` (opening movie).

## Data.cpk (verified: `tests/test_itoc.py`, full extract asserts every size)

ITOC-only CRI CPK: 3,340 files, numeric IDs, no names, `Align` 2048, files in ID order from `ContentOffset`. 1,467 are
CRILAYLA-compressed, the rest stored. `tools/itoc.py x` extracts to `work/cpk/<id>.<ext>` with `index.tsv`.

**Rebuild (verified):** `itoc.rebuild(path, {id: bytes})` copies untouched blocks and regenerates the ITOC, so no edits
gives the original archive (`tests/test_build.py`, disc SHA-1 matches). Edited files are stored raw; no CRILAYLA encoder
is needed. A file whose sizes reach 64K moves from the u16 L table to the u32 H table; the ITOC has room for about 366
such moves before `ContentOffset` shifts, which `rebuild` also handles (that shift itself has not been run in-game).
An archive that outgrows its sectors goes to the end of the image (the game opens it by path, not LBA), wasting the old
448 MB in the image; the patch stays small because those bytes are unchanged.

Proved in the engine by `tools/debug/stress_build.py`: all 1,467 compressed files stored raw, script 2149 padded from
8,064 to 70,000 bytes (so in the H table), archive moved to the end of a 1.09 GB image. `scenes.py --stages` passed 99/99
and 151/151 on it. Of the 99 scene shots, 70 match the baseline exactly; the 3 worst of the other 29, compared by eye,
are the same screens at another animation frame, the rest were not looked at. 1_01_A, the only stage using 2149, plays
its dialogue. Windowed build and real hardware not tried.

| IDs | Magic | What | State |
|---|---|---|---|
| 0, 1, 3, 146-161, 1467-1522, 2031-2049 | `FCT\0` | Container: u32 count at +4, u32 table offset at +8, then (u32 offset, u32 size) pairs. `tools/fct.py` | verified on 0, 1, 3, 3/001, 3/015 |
| 2, 4, 1523-1604, 1770-1771, 1824, 1970-2028 ... | `PTP\0` | Texture pack: u32 count at +4, u32 offsets from +0x10 | verified on 3/004 |
| 5-20, 69-110, 162-295, 1605-1712 ... | `PTX@` | Texture, see `graphics.md` | verified |
| 21-68, 111-145, 1044-1096 ... | `PTG@` | Sprite group: cell table plus embedded PTX slices. See `graphics.md` | verified: `tests/test_ptg.py` |
| 296-342 ... | `PTA\0` | Animation data plus PTX; some PTX have no palette of their own | guess |
| 343-981 | none | 639 files of big-endian offset/size tables | unknown; no real text found |
| 982-1043, 2642+ | `80 00` | CRI ADX audio | verified by CRI copyright string |
| 1713-1769 | `FPD\0` | 57 files, the same count as the event scripts: per-script picture packs | guess |
| 1826-1969 | `02 1e` | 144 files of 602 bytes | unknown |
| 2050-2065 | PNG | 16 images, 144x80 | verified |
| **2149-2205** | none | **57 event scripts** (below) | verified |
| 2206-2641 | `VPD\0` | 436 packs of ADX clips, no PTX@ in any. That they are voice is a guess from the count and size | ADX verified on 2206, 2400, 2641 |

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
Their files are in the survey in `graphics.md`.

## Event script format (verified on all 57 by `tools/evscript.py`, `tests/test_extract.py`)

- u32[0] == file size - 0x14, the offset of 5 u32. Each names a group of 9 entry points by its offset (0 = none); the first
  is usually 4, the rest of the 10-u32 header, and other groups sit between code blocks. The stage record's entry number
  picks from these (read by 0xFA1A0; it is what makes 1_05_B and 1_05_C fail, `debug.md`).
- Handler table: EBOOT 0x2AEDB8 + op * 4, called as (vm, op + 2) from 0xFAAF4. Returning 1 advances IP by the length byte.
- Bytecode: `[op u8, len u8, args]`, with these exceptions, all read from the handlers:

| Op | Form | Flow |
|---|---|---|
| 01, 03 | `01 02` | ends the thread |
| 05 | `05 06 <u32>` | goto |
| 06 | `06 02` | return |
| 07 | `07 07 00 <u32>` call; `07 04 xx yy` other forms by mode | falls through |
| 08 | `08 len <u16 var> <u32 table>` | jump by a value, no fall through |
| 09 | `09 len var count <u32 x count>` | jump if var < count, else past the table |
| 0A | `0A len var <u32 true> <u32 false>` | no fall through |
| 52, 53 | `52 02 <u32 table>`, indexed by a game variable | no fall through. The table's length isn't stored: it ends where the lowest forward target starts |
| 10 11 13-16 1D 1E 90 91 DD DF EA F0 FC | condition, then `<u32>` as the last 4 bytes (handlers call 0xFF778) | conditional jump |
| 74 | `74 len idx <NUL-terminated string>` | **inline text**, IP moves past it (handler 0x108D5C). 199 of these, unit or army names: 2 to 5 per file |

- Jumps are absolute file offsets (`IP = base + u32`, 0xFF778).
- **A message reference is `46 07 00 <u32 file offset>`** (**verified** by breakpoint on 0x28, and by the walk: all
  12,000+ land on strings). Other 0x46 forms (`46 05 02 ..`, `46 03 03`) take no string. A reference can start partway
  through a longer message (2182 0x1E10): that gets its own record.
- Layout: blocks of messages and code alternate through the file; every message block is reached only through the walk. The
  walk reaches about 2.3 MB of ops. What it can't reach: 6.7 KB of op-shaped dead code, read for references too, 0x90
  padding, a few small data tables, referenced by `62 08 .. <u32>` (unit lists, no text).
- 170 strings across scripts and FCT 3/15 have no reference in any form tried (u32 anywhere in the file, low bytes in any
  operand). Most read as real dialogue, kind `unref`: cut lines, or a form not found. Translate them anyway. The marker
  build will show if any is drawn.

**FCT 3/15 children** are the same VM: u32[0] = table size, then entry u32s (children 0-5, 9, 10); child 8 has u32[0] =
offset of a zero-ended entry list; 006 and 007 are bare strings (who indexes them, and how, isn't known: phase 5). Child
005 is 196 KB of code with no text; the walk covers all of it, which is good evidence for the opcode table above.

**Insert plan (guess until phase 5):** leave code in place, append English messages at the end of the file, repoint
each op 0x46 operand (`slots` in `script/event_*.json`). No jump changes. This needs u32[0] and its 20-byte table moved or
left at the end, and a test that the longer file fits the load buffer. Scene 1 loads at RAM 0x08B8A364; the buffer's size
is unknown. **Inline 0x74 names can't grow without moving code:** fit them in their bytes, or reassemble (the walk knows
every jump, so it is possible).

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

## English engine (`tools/vwf.py`, `tools/elfpatch.py`, `tools/insert.py`; **verified** in the marker build's tour)

Variable-width English with no change to any glyph record's size:

- **Extra font page.** Fonts 1 (20 px), 2 (18), 3 (24) each get one more PTP page holding 0x20-0x7F, drawn from `fonts/` with
  the sheets' own palette use (0 clear, 1 black outline, 2-14 grey to white). Glyph index = pages * per-page + char - 0x20. ASCII
  in these fonts goes straight there: no full-width lookup, no `!?`, `Lv`, `r.` ligatures. Shift-JIS keeps working.
- **Font 4 (12 px).** Its one PTX grows from 216 to 336 rows, with the same glyphs drawn unsmoothed in its 3 colours from cell 180
  on. ASCII goes there too, except digits, which keep the game's cells and 12 px advance: its own digits read better at this size.
- **Slots.** The window allocator's `sll s2, a1, 16` (0xA0140) is now `sll .., 18`, so every window has cols * 4 records and
  vertices. A caller's col and ncols are still cells: the printer's entry hook and the 5 range calls (0xA0248 lay out, 0xA0428
  lay out with spacing, 0xA0644 colour, 0xA079C hide, 0xA089C show, 0xA09F8 clear) multiply them by 4.
- **Pixels in the record.** Record +0 holds pixel x, not a column; the draw (0x9F860) uses it as is. The printer keeps a pen at
  0x4C(sp), unused in its frame. Each glyph's advance is stored in the record's +0x1F (high byte of the flags, whose bits 0 and 1
  are the only ones used), so the typewriter, which returns after each glyph, picks the pen up from the previous record.
- **Lay-out calls** (0xA0248, 0xA0428, 65 callers) set absolute positions per record. They now step by the advance, and a call
  starting mid-row continues from the laid-out glyph before it: some callers lay a string out cell by cell at
  x = start + i * cell (the option screen does).
- **EBOOT.** Gloria Union's layout (it loads on a Vita; issue #4): still 2 program headers, segment 0 and `p_paddr` unmoved.
  Segment 1 gets file bytes for its .bss (zeros) and the blob at vaddr 0x363000 (hooks, width tables, moved strings),
  filesz = memsz. New relocations go at the end of `.rel.linkonce.d`; those patching the blob are relative to segment 1
  (info `type | 1 << 8`). Up to v1.2-pre1 the blob was a third PT_LOAD with segment 0 shifted 0x20 and blob relocs based
  on segment 0 past its end: PPSSPP took it, real hardware gave 800200D9 / 80020001. Module size 0x39DF00.
- **Heap.** 0xEFC00 creates a 0x133D400 heap and 4 arenas: 0x580000 (FCT 3, 5.56 MB, loaded at boot; a bigger FCT 3 hangs on
  Now Loading), 0x630000, 0x600000, 0x140000. The build grows the total and arena 0 by `vwf.ARENA_GROW` = 0x30000 (FCT 3 grew
  0x21B80; build asserts it fits). Real PSP user RAM is 24 MB and real atrac/mpeg PRXs live in it (PPSSPP HLEs them), so the
  original's ~1.37 MB slack after module + heap matters: up to v1.2-pre1 the grow was 0x80000, leaving ~0.66 MB.
- **Strings.** EBOOT: moved to the new segment, every `word` and `hi`/`lo` slot rewritten and checked against the original. A lui
  shared with a non-text target stays in place, 3 such groups. Scripts: in place if it fits, else after the end of the file.
  Inline and bare strings keep their exact size, padded with spaces.

- **Font 2** is dark ink on the extras' paper, no outline: index 15 clear, 1 darkest to 14 lightest, where 0 is an opaque grey.
- **Win condition panel.** 0x12F124 (2 calls, 0x12FB9C and 0x12FC24) writes its own records instead of using the lay-out calls, and of ASCII
  it knew only `o` and `r` (+10 and +14 px); any other byte stayed hidden, so the marker showed "r oo". Now every ASCII byte uses
  the glyph's advance and the loop covers all the slots.

**Not text after all:** 0x27B1AA, 0x27B1C8, 0x27B29E (code tables the printer searches; one is byte-swapped in place at boot),
0x2B1690 (the substring pointer table, `[0x8B12C]`), 0x22EBB8 (`０１２３４５６７８９　`, the digits 0x9FD60 indexes to format a number:
the marker turned the union screen's morale into "]Theui[B"). All `kind: data` now.

**Substring table.** `{sub:nn}` and `{sub16:nnnn}` index the pointer table at 0x2B1690 in the EBOOT; defeat text is chains of these
(0x2B1C6C on), so an English line built from them has one wording per part. Translators see them as separate records.

## Fonts (FCT 3 child 1, `work/fct/00003_001/`)

| Child | Content |
|---|---|
| 000 | PTX 120x216 T4, 3 colours (clear, white, black): 180 12x12 cells of katakana, Latin, digits and a few kanji: font 4, the small names on the union and map screens. No charset: the list of 180 codes is in the EBOOT at 0x27B29E, a glyph's sheet position is its index (`%10`, `/10`). A code not in the list draws cell 0x2B |
| 001 + 002 | PTP 504x504, 504x450 T4 + charset of 1,484 codes: **18x18**, font 2 (header in the charset file: cols, rows, w, h, per page) |
| 003 + 004 | PTP 500x500 x3, 500x380 T4 + charset of 2,332 codes: **20x20**, font 1 |
| 005 + 006 | PTP 504x504, 504x96 T4 + charset of 506 codes: **24x24**, font 3 |

Charset file: u32 offset of a bucket table, then u16 Shift-JIS codes, zero-terminated. Bucket boundaries in the EBOOT at
0x27B1AA (0x824F 0x8260 0x829F 0x8340 0x839F 0x889F 0x8DB1 0x93DE 0x9680 0x9785 0x989F, **read from bytes**). Glyph index
= position in the list. The 8x8 ASCII sheet (font 0) has not been located, and which font id dialogue uses is not
confirmed (the 20 in a printer argument is a hint, not proof).

## Extraction (`tools/extract.py`, `script/*.json`, `tests/test_extract.py`)

Files: `event_<id>` (57), `fct3_15_NNN` (11), `eboot_XX` (one per 64K of vaddr, XX = vaddr >> 16), `fct1_0`. A record: `id`,
`ptr` (file offset, or vaddr = `work/exe/code.bin` offset in the EBOOT), `bytes` (with NUL), `kind`, `slots`, `jp`, `en`,
`status`. Control codes in `jp`: `{n}` 01, `{voice:3 bytes}` 02, `{sub:1}` 03, `{sub16:2}` 04, `[XX]` for a byte Shift-JIS
can't hold.

| Kind | Meaning | Translate |
|---|---|---|
| `msg` | Referenced string. Script slots = operand offsets of op 46; EBOOT slots = `{word}` or `{hi, lo}` | yes |
| `inline` | Op 74 text, slot = op offset. Limited to its bytes for now | yes |
| `bare` | FCT 3/15 children 006, 007: reached by unknown means | yes |
| `unref` | Reads as text, no reference found | yes |
| `data` | Decodes as Shift-JIS but isn't text: garbage pointer targets; FCT 1/0 effect names (undrawn so far) | no |
| `debug` | CRI middleware and printf messages with ASCII newlines: the printer can't draw these | no |

`data` was filtered by heuristic (half-width kana, stray codes, rare kanji mixed with ASCII; `looks_text`), and the marker
build is the check on it: a real line tagged `data` shows up as Japanese.

**Not in `script/`:** `PARAM.SFO` title (needs `sfo.py`, one string) and text drawn as graphics (`graphics.md`).

## EBOOT strings and free space

- Strings sit on 4-aligned starts, NUL-terminated, with 0x01 newlines. The ELF keeps its section headers and `.rel.*`
  tables (type 0x700000A0: u32 offset, u32 info; type 2 word, 5/6 hi/lo pairs), so every pointer to a string is known:
  no scanning for them, and repointing a `word` needs no relocation change (guess). Code `lui`/`addiu` pairs are in `slots`.
  A pointer can come from a struct field or table reached at run time; those still appear as relocations.
- Segment 0: vaddr 0, 2,882,720 bytes, no slack known. Segment 1: vaddr 0x2BFCA0, 516 bytes in file, 668,284 in memory.
  Some `lui` immediates look segment-1-relative: one attempt (0x8B130 + 0x2BFCA0 + 0x8804000) read zeros, so this is
  **unresolved**.
- Free space plan: Japanese takes 2 bytes per char and half-width English about 1, so in-place packing of the 180 KB
  string area plausibly fits (guess, needs counting at phase 6). Overflow: a third segment or a data file, phase 5.
- Files on disc: `iso9660.patch` appends larger files to the image end. The CPK can grow that way. Real-hardware UMD
  limits do not apply to an ISO on memory stick.
- Program header 0's `p_paddr` is the file offset of `sceModuleInfo`. The PSP kernel reads module info from there, but PPSSPP looks it up by section name, so a wrong value only breaks real hardware. Up to v1.1, `elfpatch` left it unshifted: 0x20 too low. Fixed 2026-11-10; a Vita then gave 80020001 (issue #4). Since 2026-11-11 segment 0 no longer moves, so it keeps the dump's value.
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

## Width gate (`data/windows.json`, `data/box_ids.tsv`; **measured** on the fill and torture builds)

Limits per window, in px, each with the shot it came from or the word `guess`. Dialogue is 300 px x 3 lines in font 1 (about 40 characters a
line). `data/box_ids.tsv` gives each record its window: `seen` in the print survey, or `inferred` from its block. Regenerate:

    BU_PRINTLOG=work/qa/plog python -X utf8 tools/debug/scenes.py --iso build/blaze_union_marker.iso --out work/qa/marker
    python -X utf8 tools/debug/boxes.py work/qa/plog build/blaze_union_marker.iso        # one row per caller and window
    python -X utf8 tools/debug/boxmap.py work/qa/plog                                    # data/box_ids.tsv, callers with no window
    python -X utf8 tools/debug/fillbuild.py work/qa/plog build/blaze_union_marker.iso build/fill.iso   # every box full, ending in |

`tools/debug/torture.py OUT.iso ID=TEXT ..` overrides single strings. All of 0x21-0x7E and double spaces read correctly in fonts 1-4.
Limits that are not pixels or that the build handles:

- **Item names: 35 bytes.** The book's title is `sprintf(sp+0x10, "【%s】", name)` in a 40-byte stack buffer (0x120824), 4 of them the brackets;
  a longer name ends the emulator. Other stack `sprintf`s took a 40-character name without harm in the tour: names at 0xBAED4, `%s隊`.
- **Item text wraps itself.** Same strings, two screens, line counts in tables (`vwf.WRAPS`): the equip screen 2 lines of 250 px, the book
  3 lines of 140 px. The build word-wraps for each, so these strings carry no `{n}`. The equip screen's item line isn't in any scene: no items.
- **Centring and right-anchoring by bytes.** `ready_caption` (0xC62C4), the book title and others compute x from `strlen / 2 * cell`. English runs
  under that estimate, so text sits a little off centre and never overflows on its account. Check by eye in phase 8.
- **Battle news line counter (fixed 2026-11-09, issues #1 and #2).** 0x1157D4 centres the news line with 0x9FBBC(string, sp), which writes
  each line's glyph count as a byte into the caller's 0x20-byte frame. For an ASCII byte 0x9FBBC moved the buffer pointer instead of
  counting, so every English news line ("Crooked merchant Norn driven off!!", script op 0x87 at the first boss) wrote past the frame
  over saved registers and $ra and ended the game. `vwf.count_ascii` now adds the byte's font 1 width and counts a glyph per 20 px
  (the cell the caller multiplies by), so the line is centred too. The other callers of 0x9FBBC pass no buffer.
- **A line past the window's last row (fixed 2026-11-12, issue #6).** The printer checks the row only after storing the next
  glyph (0x9EF0C), so the first glyph of a line past the last row went one record past the window's buffer (cols x K x rows records
  of 0x24 bytes): a heap overflow. PPSSPP survived it; a PSP-1000 shut down on "Morale is already at maximum" (CAUTION box 0xC3C44,
  30 cols x 2 rows, mapped to `object_text` by mistake, so the English wrapped to 3 lines). `vwf` `newline` now ends the string
  when the new row is past the last (non-typewriter calls), and window `caution` lints those strings and the skill refusals
  (table 0x278748, shown by 0x38754 in the same box). Probe: `scenes.py prep_heal_full`, and `tools/debug/caution_probe.py` (every item
  owned via save+0xC4 bits, morale poked full, breakpoint on 0x9EC34 logs each record index against the buffer's capacity).
- **Defeat text.** Table 0x2B3648 has 16-byte rows; +4 points at a one-part chain, a news line in battle, centred on the screen (0x1157D4); +0xC at a chain for the game over screen (window at 0x1161D4, 5 rows). Each part is one row, so a part that wraps pushes the last row off. The build moves that window from x=252 to x=190 (288 px). `tools/debug/defeat_parts.py` splits the two uses; the parts are shared across chains, so read a change in context with `defeat_text.py --en`.
- **Text tables to windows:** `SLOT_TABLES` in `tools/debug/boxmap.py`. Windows marked `guess` in `data/windows.json` are read from code or sized to the widest Japanese line; they haven't been measured on screen.

The ISO stays at 1.04 GB: the rebuilt Data.cpk goes after the old one (see Data.cpk above), no problem for the game; the release must check the
patch size.

## Open items for later phases

1. Script load buffer size. Record-buffer capacity is 4 x cols per row now, enough for the widest box (120 glyphs in 30 cols).
2. Speaker name source (恰幅のいい商人 on the first dialogue): the EBOOT unit table.
3. Who indexes FCT 3/15 children 006 and 007, and whether `unref` lines are ever drawn: `textcover.py` in phase 8.
