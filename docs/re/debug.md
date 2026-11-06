# Debug tool: reaching scenes (phase 2)

All vaddrs; RAM = 0x08804000 + vaddr. **`lui` values below 0x0A are relative to segment 1** (vaddr 0x2BFCA0): RAM = 0x08804000 +
0x2BFCA0 + value (**verified**: `0x808B4` read this way holds mode 7 in a dialogue). Values from 0x1B upward are segment 0.
`work/exe/dis.txt` (`tools/disall.py`) is the grep target; its `[0x...]` notes use a linear scan and can be stale after a
branch. `tools/debug/callup.py ADDR` walks jal callers up to a mode handler.

## Stage table (vaddr 0x286EC4, 153 records of 28 bytes; **verified** by warping)

`+0` u32 card PTP file (1970-2028), `+8` u32 script: low 16 bits file id (2149-2205), high bits entry point (`0x10869` = 2153
entry 1), `+0xC` u32 name pointer (`1_01_A`, `3_04_AP001`), `+0x10` u8 sequence, `+0x11`, `+0x12` u8 chapter index, `+0x14`
u32 pointer or 0, `+0x18` s16 battle id or -1 (guess from values), `+0x1A` s16. Chapter titles: table at 0x236DE4 of 59
(number string, title), `1 希望の名の下に`..`6c` at 0x236FC0.

## Top level

| What | Where |
|---|---|
| Mode | seg1 `0x808B4`, handler table at vaddr 0x270810 (43 entries, 27 and 43+ empty) |
| Request flags | vaddr 0x2707F8 |
| Game state pointer | vaddr 0x27167C; `+0x19A` s16 current stage, `+0x1B4..6` play time. Story variables via `0x4FE4(state, n)` (var 0xB = next stage, var 0xA = mode 7 exit reason) |
| Start stage | `0xA9B60(stage, 1, 0)` |
| Previous record | `[[0x27B6A4]+0x3C]` |

**Mode 0 (0x1658) is the full re-init.** It reads the flags: `0x100` restart the stage in the state (retry, no card, mode 7);
`0x200` other; `0x1000000` load; **`[0x270950] & 0x10000` starts the stage in vaddr 0x270800 and plays the chapter or stage
card** (0x1B04, nothing in the shipped game sets it). `tools/debug/warp.py` uses this, with `card=False` for the retry path.

Modes seen, **verified** by trace unless marked:

| Mode | Screen |
|---|---|
| 2 | Boot flow: logos, movie, title (0x11CDA4); after new game, prologue scroll and poem |
| 5, 6 | Chapter card (`腐敗する帝国に差す光`, waits for a press), stage card (`テンガロンの女`) |
| 7 | Event: story dialogue over the map |
| 9 | Exit of an event: switch on seg1 0x808D8 (table 0x1B16D0) |
| 14, 12 | Enter field; both go to 15. **Poke from prep to start the battle** (the real start control was not found; see below) |
| 15 | Field: `NOON / 1`, terrain 街道 10%, unit name label |
| 16 | Prep map view `ユニット配置 / Location` (sub 6 at seg1 0x874A0+1): cross goes back |
| 17 | Poked from prep: 29, 15, then 7, a map with unit labels (`出撃準備OK`) |
| 18 | Win conditions, from L in prep |
| 19, 20 | `CHARACTER SELECT` (0xC8D58): circle to cards, square map, triangle status (21, 26), L, R |
| 23 | `CARD SELECT` (0xD3380): circle picks, square back, triangle data (25) |
| 28, 29 | Poked 28 from prep, lands in 29: tactics card pick, `PLAYER'S TURN`, `タクティクスカード選択`, `ブレイズ義賊団進撃!` |

Loaders by file, walked up with `callup.py`, **not yet driven**:

| File | Code | Up to |
|---|---|---|
| 1825 game over | 0x116168 | 0x116138, called from mode 7 (0x3CD0) |
| 2112 credits | 0x12C08C | mode 36 (set at 0x11ECA4, 0x11F720) |
| 2140 tutorial | 0x100004 | 0xFFFE4, 0x109EF0 by pointer |
| 2700 extras | 0x129A6C | 0x129A14 from title (0x11CDA4) |
| 2701-2704 extras pages | 0x122D38.. | mode 4 (0x12A980; set at 0x11E74C, 0x11EAD8) |
| 1531 chapter poem | 0x838F8 | 0x83870 from 0xA7CA8, 0xA7D74 |
| 2137 resume prompt | 0xF33A0 | modes 2 and 16 |

**Don't poke a mode without its setup.** From the title, modes 3, 4, 10, 13, 31-34, 36, 38-40 end the emulator: `psp.py` then
fails with `UnicodeDecodeError ... byte 0xe9`, which is the WebSocket close frame (status 1001 = `03 E9`) read as JSON, not a
text problem. They need their module's init call first. 35 falls to 5, 37 to 2, 8 to 2. From prep (`charselect`), 28, 17, 14
and 12 work (table above); 15, 30 and 11 end the emulator.

## Requests that work from a cold boot (`warp.py - --req .. --var ..`)

- **Endings:** `--req 0x200 --var 0xb=N`: mode 0 calls 0x11EC84(module, var 0xB), mode 36. **Verified** by shots at frame ~12000:
  N=0 meadow (narration, then the CG holds), N=1 two girls in a hall, N=2 sunset, N=3 action CG. No key was pressed, so the run
  stops on the CG. **Not checked:** N above 3, and the credits (file 2112, 0x12C070 from 0x11F868): try pressing circle on the CG.
- **Story variables:** byte at state + 0x20 + n for n < 0x57 (0x4FE4, 0x4D44). Flag test 0x4BA0(state, n): bit n of the words
  from state + 0.

## Open

- **1_05_B, 1_05_C end the emulator** on the card warp (2 of 153). The other 151 reach their stage. Not diagnosed; try
  `warp(card=False)` first.
- **Game over not reached.** Mode 7 exit reason (var 0xA, jump table 0x1B16F0): reason 2 is 0x3EA8, `0x116138(.., 0xFFFF)`, file
  1825. Holding var 0xA = 2 while mashing through 1_02_A went mode 7, 9, 11 and then the emulator ended, with no game over in
  the shots of 9 and 11 (map, then black). Mode 9 switches on the same value (table 0x1B16D0: value 2 is 0x2E6C, sets 11), so
  the screen may need the value set only for mode 7, or a real defeat from the field.
- **The real battle start control was not found.** Prep has no start check in 0xC8D58 or 0xD3380 (key tests listed by address
  in those functions); six seeds of 200 random keys from `charselect` never left prep. Poking mode 14 from prep gives a working
  field. Find the real path before trusting prep-to-battle text coverage.
- **Not driven:** extras (needs its unlock on the title), tutorial, recap pages, combat and result screens, shops if any.

## Title

Boot route: `1400 -;6 start;300 -;6 start;300 -;6500 -` reaches `GAME START / LOAD DATA / CONTINUE / OPTION` (state
`work/states/title.ppst`, session `work/play/a` step 4). Before the movie ends the main loop is not running: warps there do
nothing useful beyond frame ~300, which `warp.boot` uses and works from a cold boot.
