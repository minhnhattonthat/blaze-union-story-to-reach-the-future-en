# Glossary - Blaze Union: Story to Reach the Future

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file. The lint (`tools/batches.py`) fails a line whose JP has a term here and whose English lacks it, so a row must be a form that always appears.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Garlot-san, Pamela-sama). Name order: Western (given name first).
- Romanisation source: official English names where they exist (Yggdra Union, Atlus USA), else English sources for the game (Wikipedia, artbook), else Hepburn without macrons. No earlier patch exists.
- Credits: English.
- Register: modern, plain fantasy English with each speaker's voice carried by devices, see docs/style-reference.md. Contractions are normal except for formal speakers.
- Sound effects and verbal tics: written out inline, `*hic*`, `Heh heh heh...`, not bracketed notes.
- Abbreviations: full names and terms everywhere, prefer engine changes over shortening.

## Style rules
- Punctuation: 「」 -> "...", 『』 -> '...', …… -> ..., ！？ -> !?, ～ -> ~, ― -> --. 【】 -> [ ] in help text, or drop them on titles.
- ② and ③ are the game's emphasis marks: ② = !!, ③ = !? or ?!. Use one ! where !! reads shouty in English; ③ keeps its surprise.
- Full-width digits and Latin become ASCII. ♪ ☆ ★ ■ □ ○ ● ◎ are in the font and stay. No other non-ASCII.
- Keep `{sub:..}`, `{sub16:..}`, `%s`, `%d` exactly. No suffix after a variable. No a/an before one.
- {n} only where a break must fall (poems, verse, lists). Everything else is word-wrapped by the tool to the window.

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ガーロット | Garlot | | leader of Gram Blaze; 団長 "Captain" | Galot |
| ガルカーサ | Gulcasa | | Garlot's true name; official | |
| シスキア | Siskier | | | Siscia / Shiskia |
| ジェノン | Jenon | | | |
| メデューテ | Medoute | | | Medute |
| エミリオ | Emilia | | official, Eimi's true name | Emilio |
| エイミ | Eimi | | | Amy |
| アイギナ | Aegina | | official | |
| ルシエナ | Luciana | | official | |
| ユーディ | Eudy | | official | |
| レオン | Leon | | official | |
| バルドゥス | Baldus | | official | |
| ヴェルマン | Velleman | | margrave (方伯) | Berman |
| ソルティエ | Soltier | | the emperor | |
| ネシア | Nessiah | | official | |
| ベアトリーヌ | Baretreenu | | | Beatrine |
| ジルヴァ | Zilva | | official | |
| パンドラ | Pandra | | | Pandora |
| ミゼル | Mizer | | official; はだしのミゼル "Barefoot Mizer" | Mizel |
| インザーギ | Inzaghi | | official | |
| ノルン | Norn | | | |
| デイヴィド | David | | | |
| パメラ | Pamela | | official; パメラサマ "Pamela-sama" | |
| バイフー | Byff | | | Baifu / Bifu |
| イータ | Eater | | | Eta |
| ラッセル | Russell | | official | |
| オルディーン | Ordene | | King of Fantasinia | |
| アランゼーム | Alanjame | | | |
| ラピス | Lapis | | | |
| セリカ | Cerica | | | Celica / Serica |
| スレイプ | Sleip | | | |
| ユグドラ | Yggdra | | official | |
| エレナ | Elena | | official | |
| ブロンガ | Brongaa | | the demon god; キディ・ブロンガ Kiddy Brongaa | Bronga |
| アルベルト | Albelt | | marquis | Albert |
| バリン | Balin | | duke | |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ブロンキア | Bronquia | | official | Bronchia |
| ファンタジニア | Fantasinia | | official | |
| ティエラ | Tiera | | | Tierra |
| フレアヴェルク | Flarewerk | | capital, official | |
| カローナ | Karona | | official | |
| ロスト・アリエス | Lost Aries | | | |
| カタル・ブリッジ | Catal Bridge | | | |
| トキノ | Tokino | | mountain | |
| イシュナート | Ishnart | | fortress | |
| ケルヌガ | Kernuga | | | |
| シャーミネル | Sharminel | | | |
| ニーベル | Nibel | | ニーベル街区 Nibel Quarter | |
| ネザー | Nether | | ネザー地区 Nether District | |
| イーザー | Ether | | イーザー渓谷 Ether Gorge | |
| エリス | Eris | | エリス居住区 Eris Residential Quarter | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| グラムブレイズ | Gram Blaze | | the army | |
| ブレイズ義賊団 | Blaze Justice Corps / Blaze Corps | | earlier name; Blaze Corps only in 14-byte unit names | |
| 神生教団 | Blessed Papal Army / Papal | | Papal only in 8-byte unit names | |
| タクティクスカード | Tactics Card | | | |
| スキルゲージ | Skill Gauge | | | |
| ユニオンリーダー | Union Leader | | | |
| グラン・センチュリオ | Gran Centurio | | official | |
| ショップマキナ | Shop Machina | | Machina is official | |
| エースタイプ | Ace Type | | | |
| ジェノサイド | Genocide | | battle mode | |
| グリフライダー | Griffon Rider | | unit class | |
| リップフェイク | Rip Fake | | | |
| マナストーン | Mana Stone | | | |
| オリハルコン | Orichalcum | | | |
| スウィートベリー | Sweet Berry | | | |
| アイテムブレイク | Item Break | | | |

## Decisions from earlier batches
- 団長 -> "Captain" (allies addressing Garlot); ダンチョー (Byff's and rough speakers' spelling) also "Captain".
- 方伯 -> "Margrave". 帝国 -> "the Empire", 王国 -> "the Kingdom".
- 義賊 -> "thief of justice"; ブレイズ盗賊団 (what real thieves call them) -> "the Blaze Thieves". 総隊長 -> "Commander". 教団 alone -> "the Order"; 教主様, 教祖様 -> "the Pontiff". 大将 (Pandra's men, of him) -> "boss"; Pandra's word for his enemy -> "chief".
- Not in the table because their JP also occurs in longer forms: ウルズ・ティア Urd's Tear, メリア教国 Holy Nation of Melia, ユベロン Yuberon, クレドの森 the Kred forest, ドロミノス湿地帯 Dorominos Marshes, ワドニム Wadonim, グロフ Groff, ギルギト大橋 Gilgit Bridge, アイク帝 Emperor Eik, アニス様 Anis-sama, オーガニウム Ogrenium, チカラダケ Power Cap, ココリの実 Cocori Nuts, 千年雪 Thousand-Year Snow, アイテム図鑑 Item Encyclopedia, マントラップ Man Trap, 地形スキル Terrain Skill, 地形効果 terrain effects.
- Also not in the table: 賢者の石 Philosopher's Stone, ロストマテリアル / 失われた物質 Lost Material, 草刈り鎌 Grass Sickle, 金色の麦穂 Golden Wheat Ear, ペペスの実 Pepes Nut, エレミナミント Elemina Mint, エレメント Element, 妖精樹 Fairy Tree, 魔界 Demon World, 神界 / 天界 Heaven, ビクセン兄弟 Vixen Brothers, 黒騎士 Black Knight, 屍兵 corpse soldier, きらきら金貨 Sparkling Gold Coin, 海蛇のランサー Sea Serpent Lancer, 運河の三兄弟 Canal Brothers (ゲンジ Genji, ゲンゴ Gengo, ゲンナ Genna), アセラ湖 Lake Asera, 金色のドゼウ golden loach, トキノの関所 Tokino checkpoint, イーザー桟道 Ether cliff road.
- ヒック -> *hic*. フフフ -> "Heh heh heh" (Nessiah: "Hehehe..."). ケーッケッケッケ -> "Keh-keh-keh-keh!"
