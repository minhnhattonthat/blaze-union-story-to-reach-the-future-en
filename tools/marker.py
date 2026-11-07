"""Marker text: each translatable string becomes `[id] filler` at about the Japanese line's pixel width, with its control codes
and format specifiers kept in order. Ids are short (E2149.12, F3.12, B1234) and work/marker_ids.tsv maps them to record ids."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILLER = "The quick brown fox jumps over the lazy dog and runs back again to do it all once more, then rests by the river. "
ATOM = re.compile(r"\{n\}|\{[a-z0-9]+:[0-9A-F]+\}|\[[0-9A-F]{2}\]|%[-+0-9.]*[a-zA-Z%]")
AVG = 8  # px per filler character in the 20 px font
CELL = 20
TRANSLATED = {"msg", "unref", "inline", "bare"}


def cells(s):
    """Width of Japanese text in full cells; half-width characters count half."""
    return sum(0.5 if ord(c) < 0x100 or 0xFF61 <= ord(c) <= 0xFF9F else 1 for c in s)


def marker(jp, tag):
    """The tag goes before the first text run; every run becomes filler of its own width; codes stay where they were."""
    res, pos, fill = [], 0, 0
    tag = f"[{tag}]"

    def run(v):
        nonlocal tag, fill
        if not v:
            return
        want = int(cells(v) * CELL / AVG)
        if tag:
            res.append(tag)
            want -= len(tag)
            tag = ""
        if want > 0:
            res.append(FILLER[fill % 60:fill % 60 + want])
            fill += want

    for m in ATOM.finditer(jp):
        run(jp[pos:m.start()])
        res.append(m[0])
        pos = m.end()
    run(jp[pos:])
    return tag + "".join(res)  # tag is empty unless the string held only codes


class Marker:
    """Text source for insert.build."""

    def __init__(self):
        self.ids = []
        self.n = {}

    def __call__(self, r, name):
        if r["kind"] not in TRANSLATED or not r["jp"]:
            return None
        i = self.n[name] = self.n.get(name, -1) + 1
        if name.startswith("event_"):
            tag = f"E{name[6:]}.{i}"
        elif name.startswith("fct3_15_"):
            tag = f"F{int(name[8:])}.{i}"
        else:
            tag = f"B{i}"
        self.ids.append((tag, r["id"]))
        self.tag = tag
        if r["kind"] in ("inline", "bare", "unref"):
            return self.fit(r)
        return marker(r["jp"], tag)

    def fit(self, r):
        """The last record again, cut to its own bytes: for strings that can't move."""
        return fit(r["jp"], self.tag, r["bytes"] - 1)

    def save(self):
        p = ROOT / "work/marker_ids.tsv"
        p.write_text("".join(f"{a}\t{b}\n" for a, b in self.ids), encoding="utf-8", newline="\n")


def fit(jp, tag, room):
    """Strings pinned to their bytes: the codes they carry, then as much of the tag as fits."""
    from extract import TBL
    codes = "".join(m[0] for m in ATOM.finditer(jp))
    room -= len(TBL.encode(codes))
    return codes + f"[{tag}]"[:max(room, 0)]
