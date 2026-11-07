# Graphics and the graphics-text survey

## PTX@ (verified by rendering; `tools/ptx.py`)

`+4` log2 tex w, `+5` log2 tex h, `+6` u16 stride, `+8` u16 w, `+A` u16 h, `+C` GU format (4 = T4, 5 = T8), `+D` flags (bit 0
= swizzled, 16x8-byte blocks over the stride), `+10` u32 palette count, `+14` u8 15 - log2 w, `+15` u8 15 - log2 h (the game's
UV shifts, true of all 5,820 PTX in the archive; a new width needs them rewritten), `+18` u32 palette offset, `+1C` u32 data offset.
Palette RGBA8888. **Palette offset 0 = no palette of its own**: the slice shares the previous texture's palette in the
same file. `tools/ptx.py` has no encoder yet.

## PTG@ sprite group (verified: `tests/test_ptg.py`; source rects of all 59,794 cells in 2,127 groups fit their slices)

**A PTX in a group is not an image: it is a packed atlas.** Blank space is cut out and rows are laid side by side, so an
"8-px strip" reading `X 暗黒攻撃に弱い` is really a 140x16 sprite with its lower half to the right of its upper half.
Read text through `tools/ptg.py`, never from the raw slice. A group sits right before its slices.

`+4` u32 cell table offset (0x20), `+8` u32 first PTX offset, `+C` u32 second PTX offset (0 = none), both from the PTG start,
`+10` u16 w, `+12` u16 h, `+14` u16 cells in slice 0, `+16` u16 cells in slice 1. Cell, 20 bytes: u16 sx0, sy0, dx0, dy0, zero,
sx1, sy1, dx1, dy1, pad: source rect in its own slice, destination in the sprite. 2,254 cells reach past the declared w/h;
the renderer grows the canvas to fit. The game reads the cell table at `+0x20` and ignores `+4`, so the table can't move and a
group's cell count can't grow. Its slices can: `gfx.grow` points `+8`, `+C` at new 512x8 slices at the end of a PTP file (seen in
game: Chronicle and Sound Mode titles), used when English would otherwise drop under 85%. Not for FCT 3, which isn't a PTP.

## Sweep

`python -X utf8 tools/sweep.py work/cpk work/sweep --extra work/iso/PSP_GAME/ICON0.PNG --extra work/iso/PSP_GAME/PIC1.PNG`
(~2 min) draws every PTG whole, every other PTX as is, every PNG, deduped by bytes: 2,050 groups, 1,699 PTX, 18 PNG.
- `t*.png` (9 pages): up to 24 px tall, 2x, label to the left. Read at full size.
- `s*.png` (66 pages): taller, 1x, halved when wider than 256 or taller than 200. A quarter-size overview per 4 pages was
  enough to classify; text regions were then read at full size (`tools/cropsheet.py` pastes crops into one sheet).
- `index.tsv`: page, `<file id>@<hex offset>`, drawn size.

Nothing is skipped: 184 slices with no palette are drawn in grey, label suffix `g`. 95 are PTA 300-399, the rest PTA 200-299,
1000-1410 and one in FCT 3. They read as noise (entropy about 4.9 bits per byte, T4) with no glyph shapes at any size, sit
beside the battle-unit sprites, and are taken to be animation frames. **guess**: PTA is not decoded. The marker tour would
show any text from them. PNGs in FCT 3 (`3/010-012`) were read separately: logo art plus `NO DATA`, `CONTINUE`, no Japanese.

Files that drew nothing: no PTX@, so no images, in ADX audio, VPD (2206-2641, **verified** as ADX: headers at the first two
entries of 2206, and `(c)CRI` throughout 2206, 2400, 2641), event scripts, and the table files 343-981 and 1826-1969. FPD
1713-1769 do hold PTX@ but added nothing after dedupe: **guess** they repeat the portraits of 1605-1712, as their first
texture's size suggests. No other file holds a GIM or an embedded PNG (magic scan of all of `work/cpk`; JPEG not scanned).

## English sprites (phase 8): what is done

`data/gfx.tsv` rows, drawn by `tools/gen_gfx.py` (styles: `banner`, `menu`, `panel` clear to alpha or panel colour;
`mirror` fills a box with the mirror of the far side, for symmetric art; `inpaint` fills only the white lettering and its
outline from around it; `over` draws with no clear; `vbanner` turns the English 90 degrees for vertical titles).
**A packed group holds only as much ink as its slices**: English wider or taller than the Japanese ink can fail
`gfx.repack`; `gen_gfx.fitted` then draws the English smaller (down to 50%) until it fits, and preview prints the scale.
Keep boxes to the Japanese ink in packed groups. `tools/debug/gfx_fits.py [PREFIX]` lists rows that need a shrink or fail,
`tools/debug/gfx_tight.py LABEL x0,y0,x1,y1..` gives the ink box inside a rough rect, `tools/debug/gfx_chapters.py`
regenerates the chapter card rows (titles from the EBOOT table at 0x236A04; locations in the script).

Done and seen in game (build `f14fdf34`): terrain labels both sets (3@480830-492c30 map panel, 3@4cc8e0-4d32d0
forecast), chapter cards for all 59 files (title + location, title, vertical title; stage card and field strip seen),
enemy-phase banners 21-68 (preview only: the `enemy_phase` scene shows a mission banner), button help atlas 3@faa20,
field labels 3@403560 (`非戦闘キャラクターです`, 士気 drawn small in its 16 px box, `メニュー`, `フィールドマップ確認中`,
`ステータス確認中`), plus the rows done before.

Done 2026-11-07 (third session, build `b9010597`): recap chapter titles 1531 (one 368x352 texture; the game cuts the 8 titles
by the rect table at EBOOT 0x2794E4, 8 bytes each x,y,w,h: 1 2 3 4 5 6a 6b 6c, with 5 and 6b sharing a row; nothing in the
code references the table by a lui/addiu pair, so the rects are left as they are and short rects get smaller English),
mission banner words 2066-2111 (the 110x48 kanji; the English line under each is the game's), prep banner 3@4323e0 (style
`stripe` redraws the white bar per row), result labels 3@373420 and 3@4607a0, the tag atlas 3@4768e0 (terrain, object and
weapon tags, short words per D8; weapon rects are 18 px wide, the white `Geographical Features` bar starts at x 64), Object
List names 1770@2add0 (large names right-aligned in cells), `フィールド上にオブジェクトは何もありません。` 1770@4fef0, result
atlas 1771@e0 (item/card headers, MVP and loot prompts, side victory banners), MVP `なし` 1771@1b1e0, the character name
list 1771@26dc0. Seen in game: mission banner, terrain tags, Unit Deployment, Object List, weapon tags, victory and loot.
Done 2026-11-07 (fourth session): recap narration, all 54 pages (1532-1581 `@20`, 1582-1585 `@20240`; each a 380 px wide
texture the game scrolls at 1:1), transcribed from the sprites and translated, style `page` (word-wrapped at the largest
size up to 17 px that fits the texture; `\n` in the row ends a paragraph). 1532 seen in game (`recap_2`); the rest only in
preview. 1582-1604 `@20` (240x136 in the index) are CG art with no text.
Done 2026-11-07 (fifth session): the 58 recap diagrams (1532-1577, 480x200; list `work/gfx/diag.txt`), 98 words, style
`pill`: the pill is the saturated colour that reaches outside the box, every other opaque pixel in the box is lettering
and is inpainted from the pill (alpha snapped, leaning clear), then English white-to-pill-colour with a black outline
and a 1 px white halo. Words: グラムブレイズ Gram Blaze, 反乱軍 Rebels, 盗賊団 Thieves, 賊 Bandit, 山賊 Brigands (the
script's word), 辺境警備軍 Frontier Guard, 輸送隊 Convoy, 輸送船 Transport Ship, 民兵 Militia, 預言者? Prophet?, 神生教団
Papal Army, はだしのミゼル Barefoot Mizer, 帝国軍 Imperial Army, 王国軍 Royal Army, ガルカーサ部隊 Gulcasa's Unit,
アイギナ近衛隊 Aegina's Guard, レオン, シスキア, アイギナ; `？？？` stays. Boxes: black outline next to white halo, cut
below the portrait frame (a long black run); short kanji (賊, 山賊, 帝国軍, 王国軍, 輸送船) widened to the pill. A box must
take the whole lettering, extrusion included: what is left at its edge seeds the fill. Clearing can split ink runs past a
group's cell count: `gfx.repack` then joins the narrowest gaps first (`tests/test_gfx.py`). Seen in game: `recap_2`'s
Gram Blaze diagram (warp `2_01_A --iso build/blaze_union_en.iso --route "900 -;6 circle" --frames 5400`; warp.py runs
the original ISO without `--iso`); the rest in preview. Card list 1771@36ad0 (39 rows, `name // epithet`, black on white,
styles `panel` and `panel-r`): English from the EBOOT card table at 0x2799D8 and the card poems' credits (0x261F3C..);
Rebellion's 天使長フラウヴェル has no poem record, romanised "Frauvel the Archangel". Preview only: the screen that shows
it isn't known.
Done 2026-11-07 (sixth and seventh sessions): trait lines 3@14d300-1779a0 and the 2700 copy, skill use conditions 3@3a1370-3aa270,
equip limits 2687 and 2700, unit and team names 3@177e70-19c940, the card screens 2683 (`@25b30`, `@32f30`, `@4c700`, `@551c0`,
`@5e860`, `@5f310`), 2684 (`@f0`, `@2c10`, `@3710`, `@e4b0`, `@1cc20`, `@23da0`, `@37b60`), 2687 `@260`, `@5ea0`, MEMO sheet
2642@c0 (the card screen's line that no record held; ★ can't be drawn, so its two rows keep the Japanese star), card owners
2642@d940, encyclopedia copies 2703@140bf0, `@164b50`, `@16ffb0`, `@17b410`, whole trait sheet 3@335440 (484x481), skill names
3@389080, 3@104960, 1824@b2e0 and the 38 single sprites 3@3aa5a0-3b2990, the prep location list **3@10f380** (370x198, 42 rows of
9 px: this is the "not located" vertical location), damage popups 3@53b260-54c420, prompts 3@3d8800, 3@4c5430 (`ここまでの戦いの
記録をセーブしますか?`, `次のマップに進む`: the save prompt no record held), 3@4ca450, option text 4@5e190, 4@67540, reward count
2689@20, scenario list 2690@30, difficulty 2690@13a50, extras menu 2700@90ff0, `@9c090`, `@b11b0`, `@b2620`, `@db3f0`, and 2701's
Emilio, Thortie, Rapis, Ordean redrawn to the glossary's names. Preview only unless a scene says otherwise.
Card names now follow the card art 2642@19030+ (D2): Rauher, Vise, Revellion, Mantrap, Thunder Bolt, Sand Storm, Rock Fall.
Row helpers: `tools/debug/gfx_grid.py` (list sheets, English from gfx.tsv or the script), `gfx_view.py` (sheet with ruler, `--built`
shows the English; the ruler's y 0 is the top of the sprite, 26 px below its label), `gfx_inkrows.py` (tighten rows to the ink,
needed in packed groups), `gfx_redo.py` (replace a label's rows), `near.py` (script records around a string). Sweep sizes in
`index.tsv` are half the real size for many sheets: read `sprite.image(label).size`.
Done 2026-11-07 (eighth session): credits 2112 (lone PTX, fixed canvases: small sizes, long names squeezed), tutorial 2140 (`cap`
inpaints bright lettering and the outline joined to it, up to 9 px past the box), Sound Mode tracks 2702, chronicle titles, extras
headers 2700@b5320, name list 2700@bb050, skill card captions 218-294, prompts 2683@67cb0 and 2687@bc60, 3@ff7e0, counters 3@f90c0
(the game cuts `Chosen` and `Sortie` from a rect that starts right of the Japanese ink, so they sit 4-5 px in), move tags 2687@4e280.
Still Japanese: the unit name on the equip bar (`ガーロット`, sheet not found), Japanese UI inside the tutorial's screenshots, `PIC1.PNG`,
title ruby. Check each against the survey table below.

## Survey (static sweep complete; the in-game tour in phases 5 and 8 adds to it)

Plan for all rows: redraw at the same size unless noted (D5: translate all). File 3 is the FCT, so `3@x` is a raw offset in
`work/cpk/00003.bin`. Pages are from the sweep above. Sprite counts cover every texture in that ID range, including the
few with no text.

| Element | Source | Count | Notes |
|---|---|---|---|
| Effect and trait lines with ○/×/- icon (`暗黒攻撃に弱い`, `ゲージ消耗`, `アイテム図鑑閲覧OK`) | 3@14d300-1779a0 (t000-t001); same list in cream at 2700@e9c50-112560 (t005-t006) | ~190 x 2 | Two copies: redraw both |
| Exclusive-use and equip limits (`ウィッチ専用`, `Lv5以上必要`, `18歳未満服用禁止`) | 3@3a1370-3aa270 (t002); 2687@52000-5f590 (t004); 2700@dbca0-e98b0 (t004-t005) | ~20 + ~60 + ~60 | Joke lines among them: keep the punch |
| Unit, class and team names, small | 3@1907d0-19c940 (t001-t002) | ~95 | Glossary names. Second style at 3@176xxx-18xxxx (s001) |
| Unit and team name lists | 3@177f00+ (s001), 1771@26dc0 (s032), 2683@32f30, 2683@4c700, 2683@5f310 (s053) | ~70 | `ガーロット隊` forms too. Exact offsets from `index.tsv` at redraw |
| Skill names, katakana | 3@3aa5a0-3b2990 (t002-t003), 3@104960 (s002), 3@389080 (s003), 1771@ (s032), 1824@b2xx (s033), 2684@1cc20, 2684@23da0 (s054) | ~60 x 6 | Most also exist as English sprites: `Make doll` in 1771, 2642, 2703. Check which screen uses which |
| Skill and card effect lists | 3@335440 (s003), 2642@c0 (s052), 2684@3710, 2684@e4b0 (s054), 2703@140bf0, 2703@164b60-17b410 (s058) | large sheets | Dense small text. 4+ sheets of paragraphs |
| Skill cards: English title plus Japanese caption | 216-295 (s008-s009): even IDs are the text panel, odd the card art | ~40 | Two caption lines under the title: `メイクドール`, `傀儡師エクシール`. Verse and title are English and stay. Character names need the glossary |
| Terrain labels | 3@480830-493f90 (s004), 3@4cc8e0-4d32d0 (t003) | 18 x 2 | `街道`, `荒野` etc. with percent |
| Battle and turn prompts | 3@3b30e0, 3@3ba6d0 (s003: `戦闘準備OK?`, `ターン終了OK?`), 3@3be550 (`ユニオン結成完了!`), 3@3ed0e0 (`タクティクスカード選択`, s004) | ~6 | Large lettering, tall condensed face |
| Battle result labels | 3@373420 (s003: `生存ユニット`, `ボーナス`, `部隊士気`, `能力差`, `地形効果`), 3@4607a0 (s004: `士気`, `装備`, `勝率`) | ~2 sheets | |
| Damage and status popups (`破壊ダメージ`, `士気ダメージ`, `GENアップ…`, `再起!`) | file 3, s005 rows 2-4 | ~20 | Offsets from `index.tsv` |
| Button help and menu sheets (`カーソル移動`, `ステータス`, `配置確認`, `戻る`, `勝利条件`) | 3@faa20 (s002), 3@ff7e0 (`:カードデータ`, t000), 3@403560 (`フィールドマップ確認中`, s004) | ~4 sheets | Mixed with English buttons on one atlas |
| Map legend and help panels | 3@4948f0, 3@497360, 3@499590 (s004) | 3 | `味方ユニット`, `得意`, `移動不可`… |
| Field menu | 3@467980, 3@472fa0, 3@4768e0 (s004) | 3 | `ターン終了`, `全体マップ`, `ユニットリスト`… |
| Deployment and info panels | 3@434xxx (`ユニット配置`, `ロケーション`), 3@479940 (`味方残りユニット`…, s004), 3@3d8800 (`アイテムを持っていません`, s003) | ~3 | |
| Enemy-phase banners (`ヴェルマン隊進撃!`) | 21-68 (s005) | 48 | One file per team; large lettering |
| **Chapter cards and location banners** (`義賊団参上!` / `ティエラ・ネザー地区西`) | 1970-2028 (s033-s047), one PTP per chapter | 59 chapters, 365 textures | Each has small title + location, large title, vertical title beside the map thumbnail. Map art stays |
| Chapter titles in the chronicle (`~ フレアヴェルク上洛 ~`) | 2700@1129d0-128650 (t006-t007) | ~120 | Same titles as above; keep one source of wording |
| Mission banners (`炎上`, `召喚`, with English line `-Castle on fire!-`) | 2066-2111 (s048-s049) | 46 x ~3 | Kanji word on art; English subtitle stays. 138 textures |
| **Prologue poem** (`希望の名の下に…`, with the `CHAPTER 123456` digits) | 1531 (s027) | 1 | Red/white kanji, tall lines |
| **Story recap pages and prologue scroll** (`「戦乱の渦を巻き起こす」と言い…`) | 1532-1604 (s027-s031), PTP | 132 textures | Multi-paragraph narration plus diagrams with `グラムブレイズ` labels. Largest image text in the game. Pixel font: transcribe, then redraw |
| Game over (`ゲームオーバー`, English line stays) | 1825 (s033) | 1 | |
| Map objects and objective labels (`投石器`, `門(開)`, `目標地点`), `フィールド上に…`, `義賊団勝利`, `ガーロット隊勝利` | 1770@2add0, 1770@4fef0, 1771@e0, 1771@ (s032) | ~6 | English labels sit on the same atlas |
| Staff and cast credits | 2112@27a30-79e90 (s050) | 41 | D3: English. Romanized names need a source: see `glossary.md` |
| Save/resume prompts (`ゲーム再開OK?`, `ゲーム中断OK?`) | 2137 (s050) | 2 | |
| Tutorial pages | 2140 (s051), plus `~チュートリアル~` at 2140@fe7a0 | 43 | Text mixed with diagrams and screenshots; redraw only the text, screenshots carry Japanese too |
| Reward and equip prompts (`このアイテムを報酬にしますか?`, `…装備しますか?`) | 2683@67cb0, 2687@bc60 (t004) | 2 | |
| Character and card select labels | 2683@5e860, 2683@5f310, 2683@551c0 (s053), 2684@2c10 (`並び替え`, `名前 POW MOV 使用頻度`, s054), 2687 `難易度`, `残された戦闘は…` (s055) | ~6 | |
| Extras menu | 2700@90ff0, 2700@9c090, 2700@b11b0-b5320 (`ブレイズ戦記`, `キャライラスト`, `サウンドモード`, `アイテム図鑑`, `カード図鑑`), 2700 lists (s056) | ~6 | |
| Sound-mode track names (`♪ 怒れる炎`) | 2702@494f0-5da30 (t007-t008) | ~60 | Some already English (`NanTuTTe`, `never`) |
| Lists in s026 (1522@6e170) and small rows in 2137-2140 | s026, s050 | 2 | |
| Found by the marker tour, not the printer, files not located yet: card list names and effect strip on Card Select (`シールドバリア`, `発動中、ダメージを受けない`, `使用条件`, `エースタイプが合えばOK!`), card_data's artist tag and MEMO (`■ 風魔サエザル`, `■自TEC≧敵GENで成功`), unit passives (`強攻撃ダメージ補正`, `グリフライダーに弱い`), the field panel's unit name | ? | ~300 | Same words exist as EBOOT records, so these may be drawn to a texture from text at run time: try a watch on the string first, then look for the atlas. Phase 8 lists them |
| XMB background | `PSP_GAME/PIC1.PNG` | 1 | `タクティカル・ファンタジーRPG`, tagline, 3 lines of blurb. ICON0 has only the English logo |
| Title logo katakana ruby (`ブレイズ・ユニオン`) above BLAZE UNION | file 4 (s005) | 1 | No official English version (D5): remove the ruby or keep, decide at phase 8 |
| Opening movie `Movie/BU_OP.pmf` | disc | 1 | H.264, 480x272, 1:59. Sampled every 15 s: English subtitle, no Japanese. **Not checked frame by frame** |

No Japanese: portraits (69-110, 1044-1522, 2761-2926), backgrounds (146-161, 2113-2136, 2911-2938), cards art (2644-2682,
2684-85, 2703-2728), battle units (1412-1464, 2705-2760), effects (file 1), save icons (2050-2065).
English already: title menu, `NOW TALKING...`, copyright line, R-Force logo, chapter result lines (111-145), `Fight!`,
`YOU WIN`, `PAUSE`, status names, class names in italic (2683@44170+), names at 2138 and 2701.
Magenta-background sheets (s000-s002) are the fonts already covered in `text.md`.

Corrections to earlier notes: `3@0x151CD0` is not a pair of lines `暗黒攻撃に弱い / 明光攻撃に強い`; it is the upper and lower
half of one line packed side by side. Prologue scroll and chapter cards are now located (above).
