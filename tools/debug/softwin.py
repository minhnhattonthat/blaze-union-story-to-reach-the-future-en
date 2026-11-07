"""Records with no window in data/box_ids.tsv, grouped by the pointer table that holds them, with the code that takes each table's address.
usage: softwin.py   (needs work/exe/dis.txt: tools/disall.py)"""
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import batches
import fit

GAP = 0x40  # slots further apart than this are another table

recs = [e for i, e in batches.index().items() if e.get("en") and i.startswith("eboot_") and not fit.window_of(e)[3]]
slots = sorted((s["word"], e) for e in recs for s in e["slots"] if "word" in s)
code_only = [e for e in recs if not any("word" in s for s in e["slots"])]
groups, cur = [], []
for word, e in slots:
    if cur and word - cur[-1][0] > GAP:
        groups.append(cur)
        cur = []
    cur.append((word, e))
groups.append(cur)

refs = defaultdict(list)
for line in (ROOT / "work/exe/dis.txt").read_text().splitlines():
    if m := re.search(r"[=\[]0x([0-9a-f]+)", line):
        refs[int(m[1], 16)].append(line.split()[0])


def near(lo, hi):
    """Code taking an address from just before the table to its end: indexed tables are often reached from an entry before the first."""
    return sorted({f"{a:#x}<-{c}" for a in range(lo - 0x20, hi + 4, 4) for c in refs.get(a, ())})


soft = sum(bool(fit.problems(e, e["en"])[1]) for e in recs)
print(f"{len(recs)} records, {soft} over; {len(groups)} tables, {len(code_only)} records with code slots only")
for g in groups:
    lo, hi = g[0][0], g[-1][0]
    over = sum(bool(fit.problems(e, e["en"])[1]) for _, e in g)
    print(f"\n{lo:#x}-{hi:#x} {len(g)} slots, {over} over, e.g. {g[0][1]['jp']!r} {g[-1][1]['jp']!r}")
    print("  " + " ".join(near(lo, hi)[:14]))
print("\ncode slots only:")
for e in code_only:
    print(f"  {e['id']} {e['jp']!r} {e['slots'][:2]} over={bool(fit.problems(e, e['en'])[1])}")
