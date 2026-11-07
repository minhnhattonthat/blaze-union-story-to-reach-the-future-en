"""Apply review fixes: lines of `bNNN:n<TAB>English` from a file go into each batch's .out.tsv (and .part.tsv if it has one, so tm.py keeps them), then check and merge.

    python -X utf8 tools/tlfix.py FIXES.tsv
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches


def set_lines(text, lines):
    """.out.tsv text with {n: English} replacing those line numbers."""
    rows = text.splitlines()
    seen = set()
    for i, row in enumerate(rows):
        n = int(row.split("\t")[0])
        if n in lines:
            rows[i] = f"{n}\t{lines[n]}"
            seen.add(n)
    assert seen == set(lines), f"no such lines: {sorted(set(lines) - seen)}"
    return "\n".join(rows) + "\n"


def main(path):
    fixes = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            at, en = line.split("\t", 1)
            b, n = at.split(":")
            fixes.setdefault(b, {})[int(n)] = en
    for b, lines in fixes.items():
        out = batches.TL / f"{b}.out.tsv"
        out.write_text(set_lines(out.read_text(encoding="utf-8"), lines), encoding="utf-8", newline="\n")
        part = batches.TL / f"{b}.part.tsv"
        if part.exists():
            with part.open("a", encoding="utf-8", newline="\n") as f:
                f.writelines(f"{n}\t{en}\n" for n, en in lines.items())
    return subprocess.call([sys.executable, "-X", "utf8", str(Path(__file__).with_name("batches.py")), "merge", *fixes, "--overwrite"])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
