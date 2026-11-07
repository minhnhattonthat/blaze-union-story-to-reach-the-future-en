"""Translation memory for EBOOT batches, where one line recurs under several windows: fill exact JP repeats from script/.

    python -X utf8 tools/tm.py bNNN   writes work/tl/bNNN.out.tsv with the repeats plus any lines in bNNN.part.tsv; prints what is still missing

Write the printed lines to work/tl/bNNN.part.tsv (n<TAB>English) and run it again, then `batches.py check` and `merge` as usual.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches


def memory():
    tm = {}
    for _, doc in batches.docs():
        for e in doc:
            if e.get("en") and e["jp"]:
                tm.setdefault(batches.plain_jp(e).replace("{n}", ""), e["en"])
    return tm


def fill(jps, tm, part):
    """{n: English} for line numbers from 1: part wins over memory. Returns (filled, missing line numbers)."""
    done, missing = {}, []
    for n, jp in enumerate(jps, 1):
        en = part.get(n) or tm.get(jp.replace("{n}", ""))
        if en:
            done[n] = en
        else:
            missing.append(n)
    return done, missing


def main(batch):
    rows = batches.read_tsv(batches.TL / f"{batch}.tsv")
    jps = [r[4] for r in rows]
    part_path = batches.TL / f"{batch}.part.tsv"
    part = {int(r[0]): r[1] for r in batches.read_tsv(part_path)} if part_path.exists() else {}
    done, missing = fill(jps, memory(), part)
    out = "".join(f"{n}\t{done[n]}\n" for n in sorted(done))
    (batches.TL / f"{batch}.out.tsv").write_text(out, encoding="utf-8", newline="\n")
    print(f"{batch}: {len(done)} of {len(jps)} filled, {len(missing)} left")
    last = None
    for n in missing:
        box = rows[n - 1][2:4]
        if box != last and box[0]:
            print(f"<{box[0]} {box[1]}>")
        last = box
        print(f"{n}|{rows[n - 1][1]}|{jps[n - 1].replace('{n}', '/')}")


if __name__ == "__main__":
    main(sys.argv[1])
