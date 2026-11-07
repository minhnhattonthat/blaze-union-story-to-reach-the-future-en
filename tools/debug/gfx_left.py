"""Sheets of the sprites of some files that data/gfx.tsv has no row for, to find what is still Japanese.
usage: gfx_left.py OUTDIR FILEID.. [--per N] [--max-h H] (sprites taller than H are skipped: art)"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen_gfx
import sprite

ROOT = gen_gfx.ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("ids", nargs="+", type=int)
    ap.add_argument("--per", type=int, default=40)
    ap.add_argument("--max-h", type=int, default=60)
    a = ap.parse_args()
    done = set(gen_gfx.rows())
    labs = []
    for ln in (ROOT / "work/sweep/index.tsv").read_text(encoding="utf-8").splitlines():
        f = ln.split("\t")
        if len(f) < 3 or "@" not in f[1]:
            continue
        i, o = f[1].split("@")
        if not i.isdigit() or int(i) not in a.ids or not all(c in "0123456789abcdef" for c in o):
            continue
        lab = f"{int(i)}@{o}"
        if lab not in done:
            labs.append(lab)
    Path(a.out).mkdir(parents=True, exist_ok=True)
    shown = []
    for lab in labs:
        try:
            im = sprite.image(lab)
        except Exception as e:
            print(lab, "skip", e)
            continue
        if im.height <= a.max_h and im.split()[3].getbbox():
            shown.append((lab, im))
    print(len(labs), "without rows,", len(shown), "shown")
    for p in range(0, len(shown), a.per):
        part = shown[p:p + a.per]
        W = 100 + max(i.width for _, i in part)
        H = sum(i.height + 2 for _, i in part)
        sh = Image.new("RGBA", (W, H), (92, 92, 108, 255))
        d = ImageDraw.Draw(sh)
        y = 0
        for lab, im in part:
            d.text((2, y), lab, fill=(255, 255, 0, 255))
            sh.alpha_composite(im, (100, y))
            y += im.height + 2
        sh.save(Path(a.out) / f"left_{p // a.per:02d}.png")


main()
