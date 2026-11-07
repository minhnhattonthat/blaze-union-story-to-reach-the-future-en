"""Stack sprites into labelled sheets for transcription: each sprite on grey, its label and index on the left.
usage: gfx_stack.py OUTDIR PREFIX [--size WxH] [--range LO-HI] [--per N] [--zoom Z]
PREFIX matches sweep labels in work/sweep/index.tsv (e.g. 3@14 or 2700@e9); --size keeps one sprite size only."""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sprite

ROOT = Path(__file__).resolve().parents[2]


def labels(prefix, size=None, lo=0, hi=1 << 32):
    fid, hexp = prefix.split("@")
    out = []
    for line in (ROOT / "work/sweep/index.tsv").read_text(encoding="utf-8").splitlines():
        f = line.split("\t")
        if len(f) < 3 or "@" not in f[1]:
            continue
        a, b = f[1].split("@")
        if not all(c in "0123456789abcdef" for c in b):  # suffixed labels (3aa0g) are not sprites
            continue
        if int(a) == int(fid) and b.startswith(hexp) and (size is None or f[2] == size) and lo <= int(b, 16) <= hi:
            out.append((f"{int(a)}@{b}", f[2]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("prefix")
    ap.add_argument("--size")
    ap.add_argument("--per", type=int, default=20)
    ap.add_argument("--zoom", type=float, default=2)
    ap.add_argument("--range", help="LO-HI hex offsets, inclusive")
    a = ap.parse_args()
    lo, hi = (int(v, 16) for v in a.range.split("-")) if a.range else (0, 1 << 32)
    labs = labels(a.prefix, a.size, lo, hi)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for s in range(0, len(labs), a.per):
        imgs = [(n, lab, sprite.image(lab)) for n, (lab, _) in enumerate(labs[s:s + a.per], s)]
        w = max(i.width for _, _, i in imgs)
        h = sum(i.height + 2 for _, _, i in imgs)
        sheet = Image.new("RGB", (w + 110, h), (96, 96, 112))
        d = ImageDraw.Draw(sheet)
        y = 0
        for n, lab, i in imgs:
            d.text((2, y + 2), f"{n} {lab}", fill=(255, 255, 0))
            sheet.paste(i, (110, y), i)
            y += i.height + 2
        if a.zoom != 1:
            sheet = sheet.resize((int(sheet.width * a.zoom), int(sheet.height * a.zoom)), Image.NEAREST)
        p = out / f"stack_{s // a.per:02d}.png"
        sheet.save(p)
        print(p, len(imgs))


if __name__ == "__main__":
    main()
