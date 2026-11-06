# Graphics and the graphics-text survey

## PTX@ (verified by rendering 5, 100 and 3@0x151CD0; `tools/ptx.py`)

`+4` log2 tex w, `+5` log2 tex h, `+6` u16 stride, `+8` u16 w, `+A` u16 h, `+C` GU format (4 = T4, 5 = T8), `+D` flags (bit 0
= swizzled, 16x8-byte blocks over the stride), `+10` u32 palette count, `+18` u32 palette offset, `+1C` u32 data offset.
Palette RGBA8888. **Palette offset 0 = no palette of its own**: the slice shares the previous texture's palette in the
same file. `tools/ptx.py` has no encoder yet.

## Sweep

`python -X utf8 tools/sweep.py work/cpk work/sweep` (~2 min) finds every `PTX@` by magic, dedupes by bytes, writes:
- `work/sweep/sNNN.png`: 70 pages, textures taller than 16 px, 30 per page, labelled `<file id>@<hex offset> WxH`.
- `work/sweep/tNNN.png`: 32 pages, strips up to 16 px tall, 80 per page at 2x. **These are mostly pre-rendered text**:
  e.g. 3@0x151CD0 is an 8-px strip reading `暗黒攻撃に弱い / 明光攻撃に強い`.
- `work/sweep/index.tsv`: page, cell, label. 4,738 unique textures.

Skipped, listed by the tool (184): slices with no palette and no earlier texture in that file, mostly PTA 296-342 and
1051-1410. Their palette comes from elsewhere. Not reviewed: check whether any are text (the bytes can be drawn in grey).

Not covered by the sweep: GIM/PNG inside containers other than top-level CPK PNGs (`3/010-012` are PNGs inside FCT 3,
and it searches raw bytes for `PTX@` only), and PSP_GAME/ICON0.PNG, PIC1.PNG.

## Survey: **NOT FINISHED** (phase 1 done-when)

Read all 102 sweep pages. Reading them cost too much for the worker that made them: 32 strip pages at about 2.5k tokens
each plus 70 others. Do it in chunks in a fresh context and fill the table.

| Element | Where seen | Source | Plan |
|---|---|---|---|
| Prologue scroll (ブロンキア帝国 ...) | new game, shots in session `work/play/a` | image, not in any text source; exact texture not found yet | redraw |
| Chapter title card and location banner (義賊団参上! / ティエラ・ネザー地区西) | cold boot, new game, first event | image; texture not found yet | redraw |
| Header title over the dialogue scene (義賊団参上!) | first event | image, likely same family | redraw |
| Effect/trait strips (暗黒攻撃に弱い ...) | sweep, 3@0x151CD0 onward | 8-px T4 strips with icons, many | redraw |
| Title logo katakana ruby (ブレイズ・ユニオン) above BLAZE UNION | title screen | image | Logo is otherwise English; per D5 no official English version exists, so remove the ruby or keep (decide at phase 8) |
| Opening movie BU_OP.pmf | boot | H.264, 480x272, 1:59. Frames sampled every 15 s show English subtitle `STORY TO REACH THE FUTURE` and no Japanese. **Not checked frame by frame** | probably nothing to do |

English already: title menu (GAME START, LOAD DATA, CONTINUE, OPTION), `NOW TALKING...`, copyright line, R-Force logo.
XMB: PARAM.SFO title `BLAZE UNION` is already English; ICON0.PNG and PIC1.PNG not looked at.
