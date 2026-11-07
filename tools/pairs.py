"""Review input: batches as `>> bNNN:n | speaker | window | JP` / `EN` lines, story order inside a batch, so a line's neighbours are its context.

    python -X utf8 tools/pairs.py --size 1500 --out work/qa/review   writes rNN.txt, batches kept whole, and prints what each one holds
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches

ORDER = (range(35, 132), range(132, 147), range(1, 35), range(147, 149))  # story, FCT barks, EBOOT, leftovers


def chunks(sizes, size):
    """[[name, ..], ..] from (name, rows) in order, closing a chunk once it holds `size` rows or more."""
    out, cur, n = [], [], 0
    for name, rows in sizes:
        cur.append(name)
        n += rows
        if n >= size:
            out.append(cur)
            cur, n = [], 0
    return out + [cur] if cur else out


def pairs(batch):
    names = {j: ens[0] for jps, ens, _ in batches.glossary() for j in jps}
    out = {int(r[0]): r[1] for r in batches.read_tsv(batches.TL / f"{batch}.out.tsv")}
    for n, (_, who, box, _, jp) in enumerate(batches.read_tsv(batches.TL / f"{batch}.tsv"), 1):
        yield f">> {batch}:{n} | {names.get(who, who)} | {box} | {jp.replace('{n}', '/')}\n{out.get(n, '').replace('{n}', ' / ')}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=1500)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    names = [f"b{i:03d}" for r in ORDER for i in r]
    sizes = [(b, len(batches.read_tsv(batches.TL / f"{b}.tsv"))) for b in names]
    Path(a.out).mkdir(parents=True, exist_ok=True)
    for i, group in enumerate(chunks(sizes, a.size), 1):
        text = "".join(line for b in group for line in pairs(b))
        (Path(a.out) / f"r{i:02d}.txt").write_text(text, encoding="utf-8", newline="\n")
        print(f"r{i:02d} {group[0]}-{group[-1]} {text.count('>> ')} lines")


if __name__ == "__main__":
    main()
