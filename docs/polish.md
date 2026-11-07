# Polish list

Minor fixes to make before release (phase 9 gate: no unticked line). Ids are `bNNN:n` in `work/tl/`; apply with `tools/tlfix.py`.

## From the phase 6 review (H:\translation\.harness\reviews\blaze-union-story-to-reach-the-future-en-phase6.md)

- [x] M1 (r12, 2026-11-07: 24 captions unified, one form per JP; メガネ女の大砲 left, see r11 b025:110 below). Same place, different wording, b025/b026 against b033/b034 (25 pairs): Sharminel Fort / Fort Sharminel, Pandra Fort / Fort Pandra, Deserted Manor / Deserted Mansion, Prophet's Manor / Prophet's Mansion, Glasses Woman's Cannon / Glasses Girl's Cannon, Decayed Temple / Ruined Temple, Vigilante Post / Watch Post, Rendezvous Plateau / Muster Plateau, Great Man's House / Hero's House. Pick one per place. Both tables now have room (speaker 300 px, map_ticker 540 px).
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
- [ ] r08 b134:73 後で置物にしてやるよ: "Nice ornament, you" is stiff (21-byte bare slot); find a better fit.
- [ ] r08 b127:94 unref (50 bytes): "...and charge the Sword" lost "Holy" and the trailing "..."; restore if `textcover.py` shows it drawn.
- [ ] r08 b137:58 腕一本で勝負: "fights with his bare arm alone" -> "fights with nothing but his fists".
- [ ] r08 b124:70 ギリギリの裏切り puns on 義理 (loyalty); "cutting-edge double-cross" has no pun: find an English one.
- [ ] r11 b015:41 へへへ、ヤルってことさ (means I'm good): "I'm gonna do it" -> "Heh heh heh, I've got what it takes."
- [ ] r11 b017:78 懐が浅すぎたか: "I wasn't deep enough..." -> "I lacked the depth..."
- [ ] r11 b025:36 酒場の看板娘: "Tavern Poster Girl" -> "Tavern Barmaid".
- [ ] r11 b025:110 メガネ女の大砲 "Four-Eyes' Cannon" is ruder than the label b024:121 "Woman in Glasses"; see the field-tag row below. r12: the map ticker b034:12 says "Glasses Girl's Cannon" (168 px, field tag 160): make them match.
- [ ] r12 Chronicle replay dialogue b029:12-144 differs in wording from the event copies (b040:95-100, b041:72-78 and the rest): copy the event English over where it fits.
- [ ] r07 Pamela's だわさ flattened to plain English: b112:88, b114:85, b115:52, b120:121, b121:27, b121:70, b123:22 (same as r10's deferral; pick one device and apply it to all her だわさ lines).
- [ ] r07 Byff's weaker puns: b120:27 仮定/かてぇ "That is what-iff", b120:114 復讐復讐 heard as a sneeze (English has no sound joke), b114:66 老将/朗笑 "You soldier on".
- [ ] r07 Event unit labels in byte-fixed slots: 王国軍 "Army" (b110:117-119, b112:57-58, b115:88; slots 6-26 bytes) where the EBOOT label says "Royal" (r11 b019:86), ネシア屍兵団 "Nessiah Army" (b123:76, 12 bytes, drops 屍兵). Needs the label string moved to grow. Same for r06: ヴェルマン隊A/B "Velleman A/B" (b100:139-140), ベアトリーヌ隊 "Baretreenu" (b102:120), ソルティエ皇帝隊 "Emperor Soltier" (b105:80) drop 隊 (unit).
- [ ] r06 私兵団邸 has three wordings: "the band's residence" (b099:7), "the residence" (b099:81, b100:15), "the mansion" / "the private army's mansion" (b109:48-60). Pick one.
- [ ] r06 Pamela's だわさ flattened (b101:126, b102:39-40, b107:43, b110:125), with r07's list; Aegina's contractions (b107:29, b109:16, b109:30) against her strict register.
- [ ] r01 b046:109-110 Byff's 書庫/車庫 mishearing is "library"/"livery", not a sound-alike in English: find a pair that is. b041:57 セリカの想い "Is Cerica's love not enough!?" may read as romance with David (想い = her feelings, resolve). b043:82 Jenon "That's some incredible force to break through..." is ambiguous (Leon's breakthrough power). Unit labels ジルヴァ暗殺部隊 "Zilva Assassins" (b042:126) vs ジルヴァ暗殺隊 "Zilva Assassin" (b047:95), byte-fixed.
- [ ] r12 b030:76 ひとつ覗いてみませんか (care to take a peek?) is "How about a dip?": decide in the story pass whether the content rule covers it (the bath scenes include young characters).
- [ ] r12 book text cut to 3 rows: b030:97 drops 方伯 "Margrave", b030:110 drops "to friend and foe", b030:121 drops "on his master's orders".
- [ ] r12 b032:21 これで万事解決× "All Fixed! (Not)" adds a joke the JP lacks (× is an emphasis mark): "All Fixed!!"
- [ ] r12 game over: "Garlot and the others, however, / during Round 1, / was routed by a tactical error," (b027:78 then the shared b028:60): plural subject, singular verb; b028:60 is in 80 chains.
- [ ] r10 battle cries with a speaker quirk flattened (no speaker in the record, so match the voice when the speaker is known): だわさ b008:17 "Too light.", b009:49, b013:5; かしら b009:126 "I suppose I stopped the fatal wound." -> "Looks like I dodged a fatal wound, didn't I?"
- [ ] r10 b008:33 …役不足だ (strictly: the role is beneath me) "...Not up to the task." reads as self-doubt -> "...You're no match for me."
- [ ] r10 b007:108 ピックが合いませんわ "My pick is out of tune..." (a pick isn't tuned) -> "My pick just isn't right..."
- [ ] r10 b007:53 いかがですか？ "How is this?" -> "How do you like that?"; b009:86 …感謝しよう "...I give thanks." -> "...You have my thanks."; b009:149 望むところですよ "That is just what I wished." -> "Just as I'd hoped. Hehehe..."
- [ ] r10 b009:71 遅れをとるなよ③ "Don't fall behind?!": ③ reads as a question here -> "Don't fall behind!"
- [ ] r10 b011:68 お仕置きが必要ね "You need a spanking!" -> "You need to be punished!" unless the speaker is known to be an adult teasing an adult.
- [ ] r10 Zilva-style one-word cries read flat in English: b005:65, b007:79 "...Kill." -> "...I kill."; b007:73 "...Protect.", b012:97 "...Crush.", b013:26 "...Hinder.", b014:106 "...Tear."
- [ ] r10 laughs: b005:75, b012:110 "Kekekei!" -> "Kekekeee!"

## Cut for space (D4: flagged last resort)

Engine first: wider windows and a moved window went in where they could (`data/windows.json`). What is left:

- [ ] `eboot_2602BC` b148:17 book list: "Flame Emp. Gulcasa" for 焔帝ガルカーサ (177 px in full, window 150, the list can't move past the spine at x=250).
- [ ] `eboot_234450` b021:30 item text: "Black Knight Leon's dark devil spear." drops 全てを闇に葬り去る and 秘 (secret) from 全てを闇に葬り去る悪魔の槍。黒騎士レオン愛用の秘槍. Book text is 3 lines of 140 px.
- [ ] `eboot_2344A4` b021:32 item text: "Coin honoring Gil, hero who slew the demon dragon." drops 古の時代 (ancient times).
- [ ] `eboot_232BC8` b020:48 item text: "A 1000-year blade that cuts even the formless." drops 究極 (ultimate).
- [ ] b018 card text, 2 lines of 175 px, each shortened: 35, 37, 39, 42, 53, 56, 58, 59, 69, 73, 76, 79, 81, 87 (Terrain Skill 69 now says "Swamp" for 毒沼; "Poison Swamp" needs 3 lines).
- [ ] b019 card poems 48, 55, 60, 67, 72 shortened to 4 lines of 240 px; retry at full length if phase 8 measures a wider `card_poem`.
- [ ] Names shortened for the field tag (160 px), same string as the speaker tag: 色黒の女武芸者 "Tanned Fighter" (b024:105), 商人風の青年 "Merchant Youth" (b024:124), 大将らしき無精男 "Scruffy Chief" (b024:135), 王都住民 "Royal City Resident" (b025:14), 帝都住民 "Imperial Resident" (b025:17), ニーベル街区住民 "Nibel Resident" (b025:18), ネザー地区住民 "Nether Resident" (b025:19), メガネ女の大砲 "Four-Eyes' Cannon" (b025:110), 王都の大砲 "Capital Cannon" (b025:129). If phase 8 shows these never reach the field tag, restore them.
- [ ] Chronicle text, third row 130 px beside the button prompt: `eboot_25F9C4` b029:148, `eboot_260200` b030:40, `eboot_260890` b030:78 ("want a bath" for 汗を流したい).
- [ ] 99 `unref` lines rewritten to fit their bytes: nothing is known to draw them and they have no pointer to move, so each is a tight paraphrase (`work/qa/unref_all.tsv`). `tools/insert.py` now refuses one that doesn't fit. Restore the fuller wording of any that `textcover.py` proves drawn, if a pointer turns up.
- [ ] Game over parts rephrased to one line of 288 px: b027:134, b027:147, b028:15, b028:18, b028:31, b028:51, b028:84, b028:86, b028:102, b028:128, b028:145, b028:150, b029:2.
