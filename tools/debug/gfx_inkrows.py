"""Tighten rows of a TSV to the Japanese ink of their box (packed groups hold only that much), print the new TSV.
usage: gfx_inkrows.py ROWS.tsv > TIGHT.tsv"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sprite

for ln in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    lab, box, style, jp, en = ln.split("\t")
    x, y, w, h = map(int, box.split(","))
    bb = sprite.image(lab).crop((x, y, x + w, y + h)).split()[3].point(lambda v: 255 if v > 0 else 0).getbbox()
    print(lab, f"{x + bb[0]},{y + bb[1]},{bb[2] - bb[0]},{bb[3] - bb[1]}", style, jp, en, sep="\t")
