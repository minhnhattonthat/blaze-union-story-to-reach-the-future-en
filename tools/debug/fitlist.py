"""Every line the lint rejects for width, plus the soft ones, as `bNNN:n <TAB> window limit <TAB> px <TAB> JP <TAB> EN`: the worklist for tools/tlfix.py.
usage: fitlist.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import batches
import fit

where = {}
for p in sorted(batches.TL.glob("b[0-9][0-9][0-9].tsv")):
    for n, row in enumerate(batches.read_tsv(p), 1):
        where[row[0]] = f"{p.stem}:{n}"
for i, e in batches.index().items():
    if e.get("en") and e.get("status") != "auto":
        hard, soft = fit.problems(e, e["en"])
        if hard or soft:
            font, px, rows, _ = fit.window_of(e)
            lines = fit.wrap(e["en"], font, px)
            print(f"{where.get(i, i)}\t{fit.boxes().get(i, '?')} {rows}x{px} got {len(lines)}x{max(fit.width(x, font) for x in lines)}\t{e['jp']}\t{e['en']}")
