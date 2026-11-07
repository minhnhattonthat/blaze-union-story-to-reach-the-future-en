# Translator brief - Blaze Union: Story to Reach the Future (PSP, 2010)

Tactical RPG, prequel to Yggdra Union. Young rebels against a rotten empire: warm, funny banter, then real tragedy. Translate only the batches named, one at a time, each to a passing check. No subagents.

## Read first
1. `docs/style-reference.md` (voices) 2. `glossary.md` 3. `docs/synopsis.md`

## Input: `python -X utf8 tools/batches.py show bNNN`
`n|speaker|Japanese`, with `<window rowsxpx>` shown when the window changes; a `?` limit means the window isn't known and the limit is the Japanese line's own size. `/` is a line break in the Japanese; translate the box as one utterance. Lines are in story order.

## Output: `work/tl/bNNN.out.tsv`, with your file-write tool
`n<TAB>English`, every n once, in order. ASCII plus ♪ ☆ ★ ■ □ ○ ● ◎. No voice codes, no `{n}` unless a break must fall (poems, signed quotes), since the tool wraps. Keep `{sub..}`, `%s`, `%d`.

## Validate
`python -X utf8 tools/batches.py check bNNN` until OK, then `merge bNNN`. Over-limit lines: rephrase; never abbreviate a name. Dialogue is 3 lines of 300 px, about 110 characters.

## Style
- Faithful: same information and order of ideas; adapt idiom. No added details, no notes. Wordplay keeps its punch.
- A line any speaker could have said is a mistake: see the style reference.
- Honorifics stay (Garlot-san, Pamela-sama). 団長 = Captain.
- A speaker of `？？？` or a descriptive label stays unnamed in your wording as well: no reveals.
- A sexual remark aimed at a young or young-looking character (Siskier, Aegina, Luciana, Eimi, Cerica, Pamela and the like): keep the taunt, drop the sexual content.
- Byff's puns ("なーんつって" = "Ha, just kidding") need a new English pun, not a literal line; a later line that explains the pun must match it. Other people's reactions follow your pun.
- Lint: a katakana name + 様/さん/ちゃん/殿 needs the honorific in English (Garlot-sama, Elena-dono, Viper-chan). A glossary term stays literal even in plurals ("Sweet Berry" bush, not "Sweet Berries"). Inline `<speaker>` names have a byte limit: try the short form first.
- Mistakes so far: an adult's innuendo about herself or another adult (Baretreenu, b144; Eater, b128 and b134) was sanitised; the content rule covers only young or young-looking targets, so keep the double meaning.

## Consistency
Only the controller edits `glossary.md`. Report: `NEW TERM: jp -> en`, `UNSURE: n - note`, `LONG: n - note`.
