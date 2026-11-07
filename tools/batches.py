"""Translation batches (docs/translator-brief.md): split untranslated text, check translator output, merge it back.

    python -X utf8 tools/batches.py split [--size 3500]   work/tl/bNNN.tsv and build/terms_bNNN.txt for untranslated JP
    python -X utf8 tools/batches.py show bNNN             the batch in its compact reading form: n|speaker|window|JP
    python -X utf8 tools/batches.py check [bNNN ...]      a batch's .out.tsv; with no batch, all shipped English (for check.py)
    python -X utf8 tools/batches.py merge bNNN ... [--overwrite]   check, then write the English into script/
    python -X utf8 tools/batches.py auto                  fill lines that hold only punctuation, no words to translate

Fitted from the skill's assets/batches.py. Differences: one batch line stands for every record with the same speaker, window and
Japanese, and merge fills them all; output is n<TAB>English (n = the line in the batch); `en` holds no voice code and no {n}: fit.py adds them.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fit

TL = ROOT / "work/tl"
SCRIPT = ROOT / "script"
GLOSSARY = ROOT / "glossary.md"
MAX_ENTRIES = 150
TRANSLATED = {"msg", "unref", "inline", "bare"}
TOKEN = fit.TOKEN
VARIABLE = r"%[-+0-9.]*[a-zA-Z]|\{sub[^}]*\}"
HONORIFICS = {"さん": "-san", "ちゃん": "-chan", "くん": "-kun", "君": "-kun", "様": "-sama", "殿": "-dono", "さま": "-sama"}
PUNCT = str.maketrans({"…": "...", "！": "!", "？": "?", "。": ".", "、": ",", "②": "!!", "③": "!?", "　": " ", "・": "..."})


def docs():
    for path in sorted(SCRIPT.glob("*.json")):
        yield path, json.loads(path.read_text(encoding="utf-8"))


def keep():
    p = SCRIPT / "keep_jp.txt"
    return {line.split("\t")[0] for line in p.read_text(encoding="utf-8").splitlines() if line.strip()} if p.exists() else set()


def speakers():
    p = ROOT / "data/speakers.tsv"
    return dict(line.split("\t") for line in p.read_text(encoding="utf-8").splitlines()) if p.exists() else {}


def translatable(e, kept):
    """A record whose bytes start with the 0x90 padding overlaps the real message 3 bytes on: leave it to that one."""
    return e["kind"] in TRANSLATED and e["jp"] and e["id"] not in kept and not e["jp"].startswith(("瑞垂", "吹c", "趨C"))


def plain_jp(e):
    return fit.VOICE.sub("", e["jp"], count=1) if fit.lead(e["jp"]) else e["jp"]


def key(e, who):
    return who.get(e["id"], ""), fit.boxes().get(e["id"], ""), plain_jp(e)


def only_punct(jp):
    return not re.sub(r"\{[^}]*\}|[…。、！？・　②③]", "", jp)


def encodable(char):
    return " " <= char <= "~" or char in fit.SYMBOLS


def kind(char):
    if "぀" <= char <= "ゟ":
        return "hiragana"
    if "゠" <= char <= "ヿ":
        return "katakana"
    if "一" <= char <= "鿿" or char == "々":
        return "kanji"
    return "other"


def has_term(jp, term):
    """term occurs as a whole kana or kanji run: ミン isn't in タイミング, くも isn't in ぼくも."""
    for m in re.finditer(re.escape(term), jp):
        a, b = m.start(), m.end()
        if (a == 0 or kind(jp[a - 1]) != kind(term[0])) and (b == len(jp) or kind(jp[b]) != kind(term[-1])):
            return True
    return False


def glossary():
    """[(JP forms, EN forms, avoid forms)] from glossary.md's | JP | EN | max | notes | Avoid | tables."""
    rows = []
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 2 and cells[0] not in ("JP", "") and not set(cells[0]) <= set("-: "):
            avoid = [x.strip() for x in cells[4].split("/") if x.strip()] if len(cells) > 4 else []
            rows.append(([x.strip() for x in cells[0].split("/")], [x.strip() for x in cells[1].split("/")], avoid))
    return rows


def problems(e, en, terms):
    """Hard problems, on one line of English."""
    jp = plain_jp(e)
    if not en.strip():
        return ["empty English"]
    out = []
    plain = TOKEN.sub("", en).replace("{n}", "")
    if bad := sorted({c for c in plain if not encodable(c)}):
        out.append(f"unencodable characters {bad}")
    if re.search(r"\\u[0-9a-fA-F]{4}", en) or "\t" in en:
        out.append("escape sequence or tab in the English")
    want, have = Counter(TOKEN.findall(jp)), Counter(TOKEN.findall(en))
    if want != have:
        out.append(f"control codes differ: JP {dict(want)} EN {dict(have)}")
    if re.search(f"({VARIABLE})(st|nd|rd|th)\\b", en):
        out.append('ordinal suffix after a variable (write "No. %d")')
    jp_plain = TOKEN.sub("", jp)
    for jps, ens, avoid in terms:
        if any(has_term(jp_plain, j) for j in jps) and not any(x.lower() in en.lower() for x in ens):
            out.append(f"glossary: {jps[0]} -> {ens[0]}")
        out += [f"glossary Avoid: {a}" for a in avoid if re.search(rf"\b{re.escape(a)}\b", en)]
    for jp_form, en_form in HONORIFICS.items():
        for name in re.findall(rf"([ァ-ヶー]+){jp_form}", jp_plain):
            if en_form.lower() not in en.lower():
                out.append(f"honorific {name}{jp_form} needs {en_form}")
    return out + fit.problems(e, en)[0]


def index():
    return {e["id"]: e for _, entries in docs() for e in entries}


def read_tsv(path):
    return [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def existing():
    return sorted(TL.glob("b[0-9][0-9][0-9].tsv"))


def split(size):
    """Numbers on from the last batch and leaves out ids already batched, so a repeat run can't duplicate work."""
    TL.mkdir(parents=True, exist_ok=True)
    (ROOT / "build").mkdir(exist_ok=True)
    who, kept = speakers(), keep()
    taken = {r[0] for p in existing() for r in read_tsv(p)}
    seen = set()
    n = max((int(p.stem[1:]) for p in existing()), default=0)
    entries = {e["id"]: e for _, es in docs() for e in es}
    for i in taken:
        seen.add(key(entries[i], who))
    batches, cur, chars, cur_file = [], [], 0, None
    for path, es in docs():
        for e in es:
            if not translatable(e, kept) or e.get("en") or only_punct(plain_jp(e)):
                continue
            k = key(e, who)
            if k in seen:
                continue
            seen.add(k)
            c = len(TOKEN.sub("", plain_jp(e)))
            if cur and (chars + c > size or len(cur) >= MAX_ENTRIES or (chars > size / 2 and path.stem != cur_file)):
                batches.append(cur)
                cur, chars = [], 0
            cur.append(e)
            chars += c
            cur_file = path.stem
    if cur:
        batches.append(cur)
    terms = glossary()
    for batch in batches:
        n += 1
        name = f"b{n:03d}"
        path = TL / f"{name}.tsv"
        if path.exists():
            sys.exit(f"{path} already exists")
        rows = [f"{e['id']}\t{who.get(e['id'], '')}\t{fit.boxes().get(e['id'], '')}\t{limit_label(e)}\t{plain_jp(e)}" for e in batch]
        path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        jps = " ".join(TOKEN.sub("", e["jp"]) for e in batch)
        used = [f"{j}\t{ens[0]}\n" for jpl, ens, _ in terms for j in jpl if has_term(jps, j)]
        (ROOT / f"build/terms_{name}.txt").write_text("".join(used) or "(no glossary terms)\n", encoding="utf-8", newline="\n")
    print(f"{len(batches)} new batches in {TL}, {len(taken)} ids already batched")


def limit_label(e):
    font, px, rows, known = fit.window_of(e)
    return f"{rows}x{px}" + ("" if known else "?")


def show(batch):
    """Compact form to read: speaker names in English; window only when it changes."""
    names = {j: ens[0] for jps, ens, _ in glossary() for j in jps}
    last = None
    for i, (_, who, box, lim, jp) in enumerate(read_tsv(TL / f"{batch}.tsv"), 1):
        head = "" if not box or (box, lim) == last else f"<{box} {lim}>\n"
        last = (box, lim) if box else last
        print(f"{head}{i}|{names.get(who, who)}|{jp.replace('{n}', '/')}")


def check_batch(batch, entries, terms):
    want = [r[0] for r in read_tsv(TL / f"{batch}.tsv")]
    rows = read_tsv(TL / f"{batch}.out.tsv")
    bad = []
    got = [int(r[0]) for r in rows]
    if got != list(range(1, len(want) + 1)):
        dup = sorted(i for i, c in Counter(got).items() if c > 1)
        bad.append(f"line numbers differ: {len(got)} of {len(want)}, missing {sorted(set(range(1, len(want) + 1)) - set(got))[:8]} "
                   f"duplicate {dup[:8]}")
    out = {}
    for row in rows:
        i, en = int(row[0]), "\t".join(row[1:])
        if 1 <= i <= len(want):
            out[want[i - 1]] = en
            bad += [f"{i}: {p}: {en!r}" for p in problems(entries[want[i - 1]], en, terms)]
    return bad, out


def spread(new, overwrite):
    """{id: en} from representative lines to every record with the same key. Refuses to replace English unless told to."""
    who, kept = speakers(), keep()
    entries = index()
    by_key = {key(entries[i], who): en for i, en in new.items()}
    changed = 0
    if not overwrite:
        for _, es in docs():
            for e in es:
                if e.get("en") and translatable(e, kept) and by_key.get(key(e, who), e["en"]) != e["en"]:
                    sys.exit(f"{e['id']} would lose {e['en']!r}: pass --overwrite if that is meant")
    for path, es in docs():
        touched = False
        for e in es:
            if translatable(e, kept) and key(e, who) in by_key and e.get("en") != by_key[key(e, who)]:
                e["en"], e["status"] = by_key[key(e, who)], "done"
                touched = True
                changed += 1
        if touched:
            path.write_text(json.dumps(es, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"merged: {changed} records changed")


def auto():
    kept, n = keep(), 0
    for path, es in docs():
        touched = False
        for e in es:
            if translatable(e, kept) and not e.get("en") and only_punct(plain_jp(e)):
                e["en"], e["status"] = re.sub(r"\.{4,}", "...", plain_jp(e).translate(PUNCT).replace("{n}", "")), "auto"
                touched = True
                n += 1
        if touched:
            path.write_text(json.dumps(es, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{n} punctuation-only records filled")


def stats():
    kept, total, done, chars = keep(), 0, 0, 0
    for _, es in docs():
        for e in es:
            if translatable(e, kept):
                total += 1
                done += bool(e.get("en"))
                chars += 0 if e.get("en") else len(e["jp"])
    print(f"{done}/{total} records have English; {chars} JP chars left")


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, args = argv[0], argv[1:]
    if cmd == "split":
        return split(int(args[args.index("--size") + 1]) if "--size" in args else 3500)
    if cmd == "show":
        return show(args[0])
    if cmd == "auto":
        return auto()
    if cmd == "stats":
        return stats()
    overwrite = "--overwrite" in args
    names = [a for a in args if a != "--overwrite"]
    entries, terms = index(), glossary()
    if cmd == "check" and not names:
        bad, soft = [], 0
        for i, e in entries.items():
            if e.get("en") and e.get("status") != "auto":
                bad += [f"{i}: {p}: {e['en']!r}" for p in problems(e, e["en"], terms)]
                soft += bool(fit.problems(e, e["en"])[1])
        print(f"{len(entries)} entries, {len(bad)} problems, {soft} over the Japanese line in a window not known yet")
        print("\n".join(bad[:200]))
        return 1 if bad else 0
    if cmd not in ("check", "merge") or not names:
        sys.exit(__doc__)
    new, failed = {}, 0
    for batch in names:
        bad, rows = check_batch(batch, entries, terms)
        new.update(rows)
        failed += bool(bad)
        print(f"{batch}: " + ("OK" if not bad else f"{len(bad)} problems"))
        for line in bad:
            print("  " + line)
    if failed:
        return 1
    if cmd == "merge":
        spread(new, overwrite)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
