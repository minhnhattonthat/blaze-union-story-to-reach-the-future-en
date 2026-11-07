"""Turn lines of `record id<TAB>English` into tlfix.py's `bNNN:n<TAB>English`: a record may be a repeat, so this finds the batch line that carries its key.
usage: fixids.py IN.tsv OUT.tsv   (then: tools/tlfix.py OUT.tsv)"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import batches

who, entries = batches.speakers(), batches.index()
at = {}
for p in batches.existing():
    for n, row in enumerate(batches.read_tsv(p), 1):
        if row[0] in entries:
            at[batches.key(entries[row[0]], who)] = f"{p.stem}:{n}"
out, missing = [], []
for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    if line.strip():
        i, en = line.split("\t", 1)
        k = at.get(batches.key(entries[i], who))
        if k:
            out.append(f"{k}\t{en}\n")
        else:
            missing.append(i)
Path(sys.argv[2]).write_text("".join(out), encoding="utf-8", newline="\n")
print(len(out), "lines;", "not in any batch:", missing)
