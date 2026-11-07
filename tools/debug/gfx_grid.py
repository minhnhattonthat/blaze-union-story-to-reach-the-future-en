"""data/gfx.tsv rows for a sprite that is a grid of list cells. English comes from rows already in gfx.tsv, then from
the script (exact Japanese, ignoring breaks and '/'); a line "JP<TAB>EN" sets it by hand.
usage: gfx_grid.py LABEL STYLE LIST.txt --col x,y,w,h,n [--col ..] [--cell] [--append]
LIST.txt: one Japanese string per cell, in reading order down each --col; "-" skips a cell. Each --col is n cells w x h
stacked from x,y. Box = tight ink in the cell, or the whole cell with --cell. Prints rows; --append adds them."""
import argparse
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen_gfx
import sprite

ROOT = gen_gfx.ROOT


def key(s):
    return s.replace("{n}", "").replace("/", "").replace("／", "").replace("！", "!").replace("？", "?").strip()


def known():
    out = {}
    for f in sorted(glob.glob(str(ROOT / "script/*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        for r in d if isinstance(d, list) else d.get("records", []):
            if r.get("en"):
                out.setdefault(key(r["jp"]), r["en"].replace("{n}", " ").replace("  ", " "))
    for items in gen_gfx.rows().values():  # sprite wording wins: it is the short form
        for _, _, jp, en in items:
            if en:
                out[key(jp)] = en.replace("\n", " ")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("style")
    ap.add_argument("list")
    ap.add_argument("--col", action="append", required=True)
    ap.add_argument("--cell", action="store_true")
    ap.add_argument("--append", action="store_true")
    a = ap.parse_args()
    assert a.style in gen_gfx.STYLES, a.style
    cells = []
    for c in a.col:
        x, y, w, h, n = map(int, c.split(","))
        cells += [(x, y + i * h, w, h) for i in range(n)]
    lines = [ln.rstrip("\n") for ln in open(a.list, encoding="utf-8") if ln.strip()]
    assert len(lines) <= len(cells), f"{len(lines)} strings, {len(cells)} cells"
    img, en_of, out, missing = sprite.image(a.label), known(), [], []
    alpha = img.split()[3].point(lambda v: 255 if v > 0 else 0)
    for ln, cell in zip(lines, cells):
        jp, _, en = ln.partition("\t")
        if jp == "-":
            continue
        en = en or en_of.get(key(jp))
        if not en:
            missing.append(jp)
            continue
        x, y, w, h = cell
        bb = alpha.crop((x, y, x + w, y + h)).getbbox()
        if not bb:
            sys.exit(f"{a.label}: empty cell {cell} for {jp}")
        box = cell if a.cell else (x + bb[0], y + bb[1], bb[2] - bb[0], bb[3] - bb[1])
        out.append(f"{a.label}\t{','.join(map(str, box))}\t{a.style}\t{jp}\t{en}")
    if missing:
        sys.exit("no English: " + " ".join(missing))
    print("\n".join(out))
    if a.append:
        with open(gen_gfx.TSV, "a", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
