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
- Mistakes so far: (add reviewer lessons here)

## Consistency
Only the controller edits `glossary.md`. Report: `NEW TERM: jp -> en`, `UNSURE: n - note`, `LONG: n - note`.
