# Debug tool: reaching scenes (phase 2)

All vaddrs; RAM = 0x08804000 + vaddr. **`lui` values below 0x0A are relative to segment 1** (vaddr 0x2BFCA0): RAM = 0x08804000 +
0x2BFCA0 + value (**verified**: `0x808B4` read this way holds mode 7 in a dialogue). Values from 0x1B upward are segment 0.
`work/exe/dis.txt` (`tools/disall.py`) is the grep target; its `[0x...]` notes use a linear scan and can be stale after a
branch. `tools/debug/callup.py ADDR` walks jal callers up to a mode handler.

## Stage table (vaddr 0x286EC4, 153 records of 28 bytes; **verified** by warping)

`+0` u32 card PTP file (1970-2028), `+8` u32 script: low 16 bits file id (2149-2205), high bits index into the script's 5-slot
entry table at file + u32[0] (`0x10869` = 2153 slot 1), `+0xC` u32 name pointer (`1_01_A`, `3_04_AP001`), `+0x10` u8 sequence, `+0x11`, `+0x12` u8 chapter index, `+0x14`
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
| 4 | Extras pages, from the title (below) |
| 11 | Game over (below) |
| 14, 12 | Enter field; both go to 15 |
| 15 | Field: `NOON / 1`, terrain 街道 10%, unit name label. Circle picks and moves a unit, cross unit info, triangle threat range, **L opens the Main Menu**, R next unit, square forms a union |
| 16 | Main Menu in the field (`ターン終了`..`中断セーブ`); prep map view `ユニット配置 / Location` (sub 6 at seg1 0x874A0+1) |
| 18 | Win conditions, from L in prep or the Main Menu |
| 19, 20 | `CHARACTER SELECT` (0xC8D58): circle to cards, square map, triangle status (21, 26), left equipment, right morale heal, L, R |
| 23 | `CARD SELECT` (0xD3380): circle picks, square back, triangle data (25) on a slot holding a card |
| 24 | `戦闘準備OK?` sortie prompt, with the team's total move |
| 28, 29 | Turn start: `タクティクスカード選択`, `ブレイズ義賊団進撃!`, also `ENEMY'S TURN` |
| 31, 32 | Combat, `RESULT`. The game raises the clock from 222 to 266 MHz here, which `warp.run_to` allows for |
| 34 | Victory: `義賊団勝利`, then `アイテム入手` |
| 35 | `Save the record of War.` |
| 36, 38 | Ending, credits |

Loaders by file, walked up with `callup.py`:

| File | Code | Up to |
|---|---|---|
| 1825 game over | 0x116168 | 0x116138, called from mode 7 (0x3CD0) |
| 2112 credits | 0x12C08C | mode 36 (set at 0x11ECA4, 0x11F720) |
| 2140 tutorial | 0x100004 | 0xFFFE4, 0x109EF0 by pointer |
| 2700 extras | 0x129A6C | 0x129A14 from title (0x11CDA4) |
| 2701-2704 extras pages | 0x122D38.. | mode 4 (0x12A980; set at 0x11E74C, 0x11EAD8) |
| 1531 chapter poem | 0x838F8 | 0x83870 from 0xA7CA8, 0xA7D74 |
| Recap | 0x84814 | 0x83E60 from mode 5 (0x2BB4); 0xA7CA8 from modes 2 and 35 |
| 2137 resume prompt | 0xF33A0 | modes 2 and 16 |

## Scene list (`tools/debug/scenes.py`)

One command regenerates everything: `python -X utf8 tools/debug/scenes.py --stages --jobs 6`, one emulator per scene, cold boot each,
shot in `work/qa/scenes/<name>.png`, `--states` to save `work/states/<name>.ppst`, `--list` for names. Stages are `warp_all.py`'s job.

The real battle path, **verified**: `CHARACTER SELECT`, circle, `CARD SELECT`, take a card, circle starts the sortie (`SORTIE` in
scenes.py). In 1_02_A the card limit at seg1 0x86F10+0xC is poked to 1, count at +0xD, since the limit otherwise needs the whole
hand. In the field: circle, move, circle, square to union, circle twice, combat.

- **Victory, game over, save prompt:** from the field set var 0xA and poke mode 7: 4 victory (34), 2 game over (11), 5 save
  prompt (35). Game over also needs a defeat text id in the u16 at seg1 0x88540; 0 has no text and ends the emulator, which is
  why the earlier try died.
- **Endings:** `--req 0x200 --var 0xb=N`, N = 0-22. 0-3 are the full endings (table 0x2B6480, 16-byte records), 4-22 bonus scenes
  (table 0x2B64C0, 19 records of 12 bytes, reached at 0x11F434 as N-4). Files 1582-1604.
- **Credits:** ending 0, circle on the CG, mode 38 (0x12CBA0, state byte seg1 0x842A0+0xCF, switch at 0x12CBD4). In headless they
  hold on `Making Staff` from about frame 14000: state 0x1E waits on 0x10E730, which reads as the music stream still playing (not
  traced further), and no key leaves it. `after_credits` pokes state 0x1F, the unlock notice `OPTIONに「バトルブーストの設定」が追加されました`
  shown when 0x5CA4 reports it isn't unlocked yet. 0x2CA4(.., 2) then returns to the title. **Not checked:** a real run past the
  music wait, on the windowed build.
- **Battle boost option:** byte system save + 0xA4 (0x5CA4), set when the credits end; adds a row to `OPTION` (`title_option_full`).
- **Extras:** on the title, poke 4 into the title menu item ids (seg1 0x80668+0x82), and 0xFF over the first 0x50 bytes of the
  system save at [0x271728] (the real unlock is a cleared game). Five books: illustrations, sound, chronicle, cards, items.
- **Recap:** on a chapter card, 20 presses of circle go through the title, world map, `CLOSE UP`, then the `STORY TO REACH THE
  FUTURE` recap text.

**Don't poke a mode without its setup.** From the title, modes 3, 4, 10, 13, 31-34, 36, 38-40 end the emulator: `psp.py` then
fails with `UnicodeDecodeError ... byte 0xe9`, which is the WebSocket close frame (status 1001 = `03 E9`) read as JSON, not a
text problem. They need their module's init call first. 35 falls to 5, 37 to 2, 8 to 2. From prep (`charselect`), 28, 17, 14
and 12 work; 15, 30 and 11 end the emulator.

## Requests that work from a cold boot (`warp.py - --req .. --var ..`)

- **Endings:** `--req 0x200 --var 0xb=N`: mode 0 calls 0x11EC84(module, var 0xB), mode 36.
- **Story variables:** byte at state + 0x20 + n for n < 0x57 (0x4FE4, 0x4D44). Flag test 0x4BA0(state, n): bit n of the words
  from state + 0.

## Limits

- **1_05_B, 1_05_C can't be reached by any play route; they are left out of `warp_all.py`.** Their records use slots 1 and 2 of the
  entry table at file + u32[0] of script 2153, and those slots are 0. 0xFA0DC starts the VM at 0 and the emulator ends. **Verified**
  on all 153 records: these are the only two on an empty slot. Winning 1_05_A goes on to 1_06_A. Their header offsets (u32[2..3] =
  0x1943, 0x1A1F) are nonzero, so if phase 8's `textcover.py` lists text from there it is unused.
- **Save lists with data not shot:** the memstick starts empty, so `title_load` and `save_dialog` show `NO DATA`.
- **Scenes prove the screen, not every page in it:** the extras books, unit lists and credits have further pages. `textcover.py`
  in phase 8 turns what's missing into new entries.
- **Not yet in the list:** the reward prompt (`このアイテムを報酬にしますか?`, 1_02_A's victory has no loot), mission banners that only
  fire in later stages, skills and card effects other than 1_02_A's.

## Title

Boot route: `1400 -;6 start;300 -;6 start;300 -;6500 -` reaches `GAME START / LOAD DATA / CONTINUE / OPTION` (state
`work/states/title.ppst`, session `work/play/a` step 4). Before the movie ends the main loop is not running: warps there do
nothing useful beyond frame ~300, which `warp.boot` uses and works from a cold boot.
