#!/bin/bash
# Independent read-only review with codex, one report per pairs file; a report that exists is kept. usage: tools/review.sh [PARALLEL]
# First: python -X utf8 tools/pairs.py --size 1500 --out work/qa/review
one() {
  [ -s "work/qa/review/$1.report.md" ] && return 0
  codex exec -s read-only --skip-git-repo-check --ephemeral -o "work/qa/review/$1.report.md" "You are a read-only reviewer of a Japanese to English game translation. Read docs/reviewer-brief.md and follow it, then glossary.md, docs/style-reference.md, docs/synopsis.md and docs/translator-brief.md. Then read ALL of work/qa/review/$1.txt in passes: entries are '>> bNNN:n | speaker | window | Japanese' followed by the English; use bNNN:n as the id. Lines are in story order, so neighbours are context; windows map_ticker, battle_cry and book_* are short UI strings.

Deliberate rules, do not report them as errors: a sexual remark aimed at a young or young-looking character keeps the taunt and drops the sexual content; a speaker labelled ??? stays unnamed; Byff's puns are new English puns, not literal; text must fit its window, so short UI strings are terse and may lose small details; circled 2 and 3 in the Japanese are emphasis marks.

Also report any line where Soltier calls himself 'we' (he uses plain 'I'), and any spelling of a name or term that differs from glossary.md.

Be strict about what is Critical or Important: only real mistranslation, wrong speaker or addressee, glossary breach, or a voice or joke actually lost. List at most 25 Minors, the most useful ones. Do not edit any file. Your final message is the report, in the format the brief gives, ending with the Assessment."
}
export -f one
ls work/qa/review/r*.txt | xargs -n1 basename | cut -d. -f1 | xargs -P "${1:-4}" -I{} bash -c 'one {}'
