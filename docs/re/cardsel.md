# Card Select panel text (tools/cardsel.py)

The panel under the card grid shows the card's effect (x 21, y 212) and use condition (x 89, y 229, after the `Conditions` tag).
The original draws both as picture strips with the sprite draw 0x98798; we draw them with the font printer instead (D18).

## What the original draws (vaddr; RAM = 0x08804000 + vaddr)
- 0xD1F94: per frame, `lbu a1, 0(s1)` bit 0 = the cursor is on a card; s1 -> the slot, +6 = card number.
- 0xD201C..0xD206C: condition. Rect = 0x2898DA + card * 8 (x, y, w, h in 2684@37b60: 14 px rows, second column at x 203),
  texture 0xA, drawn at x 0x59, y 0xE5. Cards 25-28 (terrain skills) and others point at the last row, "Ace Types must match".
- 0xD20B0..0xD2124: effect. card < 20: 2684@3710 row card; else 2684@e4b0 row card - 20 (15 px rows). Drawn at x 0x15, y 0xD2.
  39 cards (0-38); the rect table holds no more.
- Card Select's window handle: 0x4F0(object). Window flags +0x34: bit 2 set = drawn. 0xD2438 hides the window (clears bit 2).
- 0xD3204 creates the window, 0xD02D4 frees it.

## The hooks
| site | replaced | does |
|------|----------|------|
| 0xD3204 | `addiu a2, zero, -5` | `init`: our own printer window (15 x 4 cells, font 1, 0x9E490 + 0xA0130), hidden |
| 0xD02D4 | `addiu a1, zero, -3` | `free`: frees it (0x9E56C) |
| 0xD2438 | `ori a3, zero, 0` (j) | `hide`: hides both windows |
| 0xD1F94 | `lbu a1, 0(s1)` | `pre`: hides ours each frame; `text` shows it again on a card slot |
| 0xD201C | `lhu a0, 6(s1)` | `text`: on a new card clears (0xA09A0), prints effect in row 0 and condition in row 2 (0x9E8DC), tints rows 2-3 red (0xA0644, ABGR 0xFF6868FF), lays each out at the strip's place (`flow`); returns past the condition draw |
| 0xD20E0 | `lhu a0, 6(s1)` | `skip`: past the effect strip draw |

The English is a table appended after the code: per card two u16 offsets (effect, condition), then the strings. `table()` builds it
from the strip rows of `data/gfx.tsv` with the game's own mapping above, and asserts each line fits (effect 280 px, condition
211 px in font 1). The EBOOT skill text (0x279C8C, getters 0x86EC4 / 0x86F0C) is Card Data's two-line wording: up to 337 px
on one line, too wide here.
