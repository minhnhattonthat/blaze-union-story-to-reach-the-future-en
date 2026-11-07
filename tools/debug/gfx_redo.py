"""Replace all of data/gfx.tsv's rows for the labels in a TSV of new rows (same five columns).
usage: gfx_redo.py NEW.tsv"""
import sys
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "data/gfx.tsv"
new = Path(sys.argv[1]).read_text(encoding="utf-8").strip() + "\n"
labels = {ln.split("\t")[0] for ln in new.splitlines()}
old = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.split("\t")[0] not in labels]
p.write_text("\n".join(old) + "\n" + new, encoding="utf-8", newline="\n")
print(len(old), "kept,", new.count("\n"), "new for", sorted(labels))
