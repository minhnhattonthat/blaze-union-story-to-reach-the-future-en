"""Print data/gfx.tsv rows for 2112's credit sprites: each block's text lines evenly spaced, as the Japanese.
usage: gfx_credits.py LIST.txt > rows.tsv
LIST: "@HEX" opens a sprite, then one line per text line: "*" marks a role, blank is a blank line (a "-" row)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sprite


def main():
    blocks, cur = [], None
    for ln in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
        if ln.startswith("@"):
            cur = []
            blocks.append((f"2112{ln}", cur))
        else:
            cur.append(ln)
    for lab, lines in blocks:
        while lines and not lines[-1]:
            lines.pop()
        w, h = sprite.image(lab).size
        n = len(lines)
        ys = [round(i * h / n) for i in range(n + 1)]
        for i, t in enumerate(lines):
            box = f"0,{ys[i]},{w},{ys[i + 1] - ys[i]}"
            if not t:
                print(f"{lab}\t{box}\tcredit\tblank\t-")
            elif t.startswith("*"):
                print(f"{lab}\t{box}\tcredit-role\tcredit role\t{t[1:]}")
            else:
                print(f"{lab}\t{box}\tcredit\tcredit name\t{t}")


main()
