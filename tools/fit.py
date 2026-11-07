"""English text layout: word wrap by the fonts' pixel widths, per window (data/windows.json, data/box_ids.tsv). The lint and the build
both use this, so what passes the lint is what the game prints. `python -X utf8 tools/fit.py "text" --box dialogue` is the dry run.

`en` in script/*.json holds no leading voice code and no {n} unless a break must fall there; wrapped() adds both.
"""
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
VOICE = re.compile(r"\{voice:[0-9A-Fa-f]+\}")
# codes that must survive translation; a leading voice code is handled by wrapped()
TOKEN = re.compile(r"\{(?!n\})[a-z0-9]+:[0-9A-Fa-f]+\}|\[[0-9A-F]{2}\]|%[-+0-9.]*[a-zA-Z%]")
ITEM_TEXT = (0x28C040, 0x28C8E8)  # vwf.WRAPS: the build word-wraps these per screen, they carry no {n}
PLACEHOLDER_PX = 60  # shortcut: %s and {sub} measured as 60 px; phase 8 reads the real lines on screen
SYMBOL_PX = 16  # the kept Shift-JIS symbols keep their game cell, about this wide
SYMBOLS = "♪☆★■□○●◎"


@lru_cache(maxsize=None)
def tables():
    import vwf
    return vwf.widths()


@lru_cache(maxsize=None)
def windows():
    return {w["name"]: w for w in json.loads((ROOT / "data/windows.json").read_text(encoding="utf-8"))}


@lru_cache(maxsize=None)
def boxes():
    """{record id: window name} from data/box_ids.tsv."""
    return dict(line.split("\t")[:2] for line in (ROOT / "data/box_ids.tsv").read_text(encoding="utf-8").splitlines())


def width(s, font=1):
    w, n, pos = tables()[font], 0, 0
    for m in TOKEN.finditer(s):
        n += sum(w[ord(c)] if ord(c) < 0x80 else SYMBOL_PX for c in s[pos:m.start()]) + PLACEHOLDER_PX
        pos = m.end()
    return n + sum(w[ord(c)] if ord(c) < 0x80 else SYMBOL_PX for c in s[pos:])


def wrap(s, font, px):
    """Lines of s: {n} is kept, the rest is greedy by words."""
    lines = []
    for part in s.split("{n}"):
        cur = ""
        for word in part.split(" "):
            test = f"{cur} {word}" if cur else word
            if cur and width(test, font) > px:
                lines.append(cur)
                cur = word
            else:
                cur = test
        lines.append(cur)
    return lines


def jp_cells(jp):
    """(px at the game's 20 px cell, lines) of a Japanese string: the safe size when the window isn't known."""
    lines = TOKEN.sub("", VOICE.sub("", jp)).split("{n}")
    return max(sum(10 if ord(c) < 0x100 else 20 for c in line) for line in lines), len(lines)


def window_of(r):
    """(font, px, rows, known). An unknown window takes the Japanese line's own size, always safe, often too strict."""
    w = windows().get(boxes().get(r["id"], ""))
    if w:
        return w["font"], w["px"], w["rows"], True
    px, rows = jp_cells(r["jp"])
    return 1, max(px, 60), rows, False


def is_item_text(r):
    return r["id"].startswith("eboot_") and ITEM_TEXT[0] <= r["ptr"] < ITEM_TEXT[1]


def lead(jp):
    m = VOICE.match(jp)
    return m[0] if m else ""


def wrapped(r, en=None):
    """The string to insert: the record's voice code, then the English with its breaks."""
    en = r["en"] if en is None else en
    if is_item_text(r):
        return en
    font, px, _, _ = window_of(r)
    return lead(r["jp"]) + "{n}".join(wrap(en, font, px))


def problems(r, en):
    """Over the window: (hard, soft) lists. Soft: the window isn't known yet."""
    font, px, rows, known = window_of(r)
    if is_item_text(r):
        if "{n}" in en:
            return ["item text takes no {n}"], []
        bad = [f"over {n} lines of {p}" for n, f, p in ((2, 1, 250), (3, 2, 140)) if len(wrap(en, f, p)) > n]
        return bad, []
    out = []
    lines = wrap(en, font, px)
    if len(lines) > rows:
        out.append(f"{len(lines)} lines, window {boxes().get(r['id'], '?')} has {rows}")
    wide = max(width(line, font) for line in lines)
    if wide > px:
        out.append(f"{wide} px, limit {px}")
    limit = windows().get(boxes().get(r["id"], ""), {}).get("bytes")
    if limit and len(en) > limit:
        out.append(f"{len(en)} bytes, limit {limit}")
    if r["kind"] in ("inline", "bare") and len(lead(r["jp"])) // 2 + len(en) > r["bytes"] - 1:
        out.append(f"{len(en)} bytes, slot holds {r['bytes'] - 1}")
    return (out, []) if known else ([], out)


def _selftest():
    assert wrap("a{n}b", 1, 300) == ["a", "b"]
    long = "the quick brown fox jumps over the lazy dog and runs back again to do it all once more"
    lines = wrap(long, 1, 300)
    assert len(lines) > 1 and all(width(x) <= 300 for x in lines) and " ".join(lines) == long
    assert width("%s") == PLACEHOLDER_PX and width("{sub:12}") == PLACEHOLDER_PX
    assert jp_cells("{voice:005000}あa{n}あ") == (30, 2)
    assert lead("{voice:005000}x") == "{voice:005000}" and lead("x") == ""
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--selftest"]:
        _selftest()
    else:
        w = windows()[a[a.index("--box") + 1] if "--box" in a else "dialogue"]
        lines = wrap(a[0], w["font"], w["px"])
        print(f"{len(lines)} lines, window has {w['rows']}, {w['px']} px")
        for line in lines:
            print(f"{width(line, w['font']):4d} {line}")
