# Polish list

Minor fixes to make before release (phase 9 gate: no unticked line). Ids are `bNNN:n` in `work/tl/`; apply with `tools/tlfix.py`.

## From the phase 6 review (H:\translation\.harness\reviews\blaze-union-story-to-reach-the-future-en-phase6.md)

- [ ] M1. Same place, different wording, b025/b026 against b033/b034 (25 pairs): Sharminel Fort / Fort Sharminel, Pandra Fort / Fort Pandra, Deserted Manor / Deserted Mansion, Prophet's Manor / Prophet's Mansion, Glasses Woman's Cannon / Glasses Girl's Cannon, Decayed Temple / Ruined Temple, Vigilante Post / Watch Post, Rendezvous Plateau / Muster Plateau, Great Man's House / Hero's House. Pick one per place. Both tables now have room (speaker 300 px, map_ticker 540 px).
- [ ] M2. Chapter titles differ between their two tables (`eboot_236AF8` Those Who Take and Are Taken From, `eboot_25FB60` Takers and Taken; also `eboot_236A90`, `eboot_236AA0`, `eboot_236ACC`, `eboot_236AE4`, `eboot_236DB8` and twins). The save table now has 430 px; the book list has 150, so the short form may have to stay there.
- [ ] M3. `docs/style-reference.md:21` and `:27`: two conflicting Mizer rows. Mizer's lines follow `:27`; delete or relabel `:21`.
- [ ] M4. Cerica says "I" where the style reference says never: `event_2199_00A1B`, `event_2165_0083D`, `event_2171_027AD`.
- [ ] M5. Glossary forms not used: 神界 "divine realm" `event_2177_0A638` (Heaven); 義賊 "noble thief" `eboot_2B57E8`, `event_2151_011BE` (thief of justice); 金色の麦穂 "golden ear of wheat" `event_2176_01C18` (Golden Wheat Ear).
- [ ] M6. Wording: b060:28 "what our employer had stolen" -> "what was stolen from our employer"; b116:32 "the King of the Kingdom"; b135:79 "The range and positions for combo attacks, the formation types, come in two kinds in all."
- [ ] M7. Lint gaps: about 70 terms live in prose at `glossary.md:103`, `:104`, `:108`, out of the lint's sight; the no-batch `check` in `tools/batches.py` skips empty `en`, so `tools/check.py` stays green if a record loses its English.
- [ ] M8. `docs/translator-brief.md:25` still reads "(add reviewer lessons here)"; add a `CUT:` report line at `:28`.
- [ ] M9. Add open rows to `docs/decisions.md`: unit-name short forms (Blaze Corps, Papal, Baldus Steel), 屍兵 "Corpse" (`eboot_25996C`, b024:49), and the content rule now only in the brief and `docs/status.md`.
- [ ] M10. Glossary tidying: カローナ is "official" at `glossary.md:67` and a guess at `:108`; about 25 place names and ブライ Bly are marked guesses.

## From the per-chunk reviewer pass (docs/review.md)

- [ ] r09 b141:22 赤髪 "Red": glossary has "Red" for Pandra and Leon, "the redhead" for Soltier; confirm this item-use block's speaker and match.

## Cut for space (D4: flagged last resort)

Engine first: wider windows and a moved window went in where they could (`data/windows.json`). What is left:

- [ ] `eboot_2602BC` b148:17 book list: "Flame Emp. Gulcasa" for 焔帝ガルカーサ (177 px in full, window 150, the list can't move past the spine at x=250).
- [ ] `eboot_234450` b021:30 item text: "Black Knight Leon's dark devil spear." drops 全てを闇に葬り去る and 秘 (secret) from 全てを闇に葬り去る悪魔の槍。黒騎士レオン愛用の秘槍. Book text is 3 lines of 140 px.
- [ ] `eboot_2344A4` b021:32 item text: "Coin honoring Gil, hero who slew the demon dragon." drops 古の時代 (ancient times).
- [ ] `eboot_232BC8` b020:48 item text: "A 1000-year blade that cuts even the formless." drops 究極 (ultimate).
- [ ] b018 card text, 2 lines of 175 px, each shortened: 35, 37, 39, 42, 53, 56, 58, 59, 69, 73, 76, 79, 81, 87 (Terrain Skill 69 drops the terrain's name from the title line, keeps it on line 2).
- [ ] b019 card poems 48, 55, 60, 67, 72 shortened to 4 lines of 240 px; retry at full length if phase 8 measures a wider `card_poem`.
- [ ] Names shortened for the field tag (160 px), same string as the speaker tag: 色黒の女武芸者 "Tanned Fighter" (b024:105), 商人風の青年 "Merchant Youth" (b024:124), 大将らしき無精男 "Scruffy Chief" (b024:135), 王都住民 "Royal City Resident" (b025:14), 帝都住民 "Imperial Resident" (b025:17), ニーベル街区住民 "Nibel Resident" (b025:18), ネザー地区住民 "Nether Resident" (b025:19), メガネ女の大砲 "Four-Eyes' Cannon" (b025:110), 王都の大砲 "Capital Cannon" (b025:129). If phase 8 shows these never reach the field tag, restore them.
- [ ] Chronicle text, third row 130 px beside the button prompt: `eboot_25F9C4` b029:148, `eboot_260200` b030:40, `eboot_260890` b030:78 ("want a bath" for 汗を流したい).
- [ ] 99 `unref` lines rewritten to fit their bytes: nothing is known to draw them and they have no pointer to move, so each is a tight paraphrase (`work/qa/unref_all.tsv`). `tools/insert.py` now refuses one that doesn't fit. Restore the fuller wording of any that `textcover.py` proves drawn, if a pointer turns up.
- [ ] Game over parts rephrased to one line of 288 px: b027:134, b027:147, b028:15, b028:18, b028:31, b028:51, b028:84, b028:86, b028:102, b028:128, b028:145, b028:150, b029:2.
