"""Which sprite holds this bit of a screenshot? Template match (normalised correlation) of a crop on every swept sprite.
usage: gfx_find.py SHOT.png x,y,w,h [--top N] [--files A-B] -> best matches: score, label, x, y in the sprite (for rows)"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.signal import fftconvolve

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sprite

ROOT = Path(__file__).resolve().parents[2]


def flat(im):
    """Sprite over black as luma: the shot's lettering sits on dark bars, and bright ink carries the match."""
    a = np.asarray(im.convert("RGBA")).astype(float)
    return (a[..., :3].mean(axis=2)) * (a[..., 3] / 255)


def match(img, t):
    """Peak normalised correlation of template t (zero mean) in img, and where."""
    h, w = t.shape
    if img.shape[0] < h or img.shape[1] < w:
        return -1, 0, 0
    c = fftconvolve(img, t[::-1, ::-1], mode="valid")
    s1 = fftconvolve(img, np.ones(t.shape), mode="valid")
    s2 = fftconvolve(img * img, np.ones(t.shape), mode="valid")
    var = np.maximum(s2 - s1 * s1 / t.size, 1e-3)
    r = c / np.sqrt(var * (t * t).sum())
    y, x = np.unravel_index(np.argmax(r), r.shape)
    return float(r[y, x]), int(x), int(y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shot")
    ap.add_argument("box")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--files")
    a = ap.parse_args()
    x, y, w, h = map(int, a.box.split(","))
    t = np.asarray(Image.open(a.shot).convert("RGB").crop((x, y, x + w, y + h))).astype(float).mean(axis=2)
    t = t - t.mean()
    lo, hi = map(int, a.files.split("-")) if a.files else (0, 1 << 30)
    out = []
    for ln in (ROOT / "work/sweep/index.tsv").read_text(encoding="utf-8").splitlines():
        f = ln.split("\t")
        if len(f) < 3 or "@" not in f[1]:
            continue
        i, o = f[1].split("@")
        if not i.isdigit() or not lo <= int(i) <= hi or not all(c in "0123456789abcdef" for c in o):
            continue
        lab = f"{int(i)}@{o}"
        try:
            s, px, py = match(flat(sprite.image(lab)), t)
        except Exception:
            continue
        out.append((s, lab, px, py))
    for s, lab, px, py in sorted(out, reverse=True)[:a.top]:
        print(f"{s:.3f}\t{lab}\t{px},{py}")


main()
