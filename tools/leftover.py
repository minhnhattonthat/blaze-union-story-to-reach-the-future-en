"""Leftover lint for data/gfx.tsv (D16): pieces of the Japanese left standing beside the English.
A blob of the original sprite's ink (8-connected alpha) that the English mostly replaced but not wholly leaves its
unchanged part on screen: a glyph's outline or a neighbouring line cut by a box drawn too tight. Flags blobs with
2 to 80 unchanged pixels (or a fifth of the changed part) that are at most the changed part; larger kept parts are
art the box only grazes. With the rows' boxes, only pixels outside every box count (gen_gfx.english sweeps them).
usage: leftover.py [LABEL..]   -> label, kept px, bbox of the kept part; exit 1 if any
library: stray(orig, new) -> [(kept px, (x0, y0, x1, y1))]"""
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).parent))

MIN_PX, MAX_PX = 2, 80


def stray(orig, new, boxes=None):
    """boxes: (x, y, w, h) the rows drew in; a piece inside any is skipped, since English can match the old ink."""
    a = np.asarray(orig.convert("RGBA")).astype(int)
    b = np.asarray(new.convert("RGBA")).astype(int)
    changed = np.abs(a - b).max(-1) > 8
    lab, n = ndi.label(a[..., 3] > 0, structure=np.ones((3, 3)))
    if not n:
        return []
    idx = range(1, n + 1)
    nch = ndi.sum(changed, lab, idx)
    nkept = ndi.sum(~changed, lab, idx)
    # shadows join a block of lines into one blob, so the cap grows with the part the English replaced
    part = [i for i, c, k in zip(idx, nch, nkept) if c and MIN_PX <= k <= max(MAX_PX, c / 5) and k <= c]
    inbox = np.zeros(changed.shape, bool)
    for x, y, w, h in boxes or ():
        inbox[max(y, 0):y + h, max(x, 0):x + w] = True
    # unchanged pixels inside a box may be English that matches the old ink by chance, so only pixels outside every
    # box count; a piece is debris if it stands alone in the new sprite, or is a sliver (<= 3 px deep) a box edge
    # cut off a glyph. An icon beside a box (wider and deeper) stays.
    kept = np.isin(lab, part) & ~changed & ~inbox
    klab, kn = ndi.label(kept, structure=np.ones((3, 3)))
    nlab, _ = ndi.label(b[..., 3] > 0, structure=np.ones((3, 3)))
    out = []
    for j in range(1, kn + 1):
        comp = klab == j
        k = int(comp.sum())
        if k < MIN_PX:
            continue
        ys, xs = np.nonzero(comp)
        sliver = min(np.ptp(xs), np.ptp(ys)) + 1 <= 3
        host = np.isin(nlab, np.unique(nlab[comp]))
        alone = k >= 0.8 * host.sum()
        if sliver or alone:
            out.append((k, (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), comp))
    return sorted(out, key=lambda t: t[1])


def sweep(orig, new, boxes):
    """Clear the pieces stray() finds outside every box from new (an RGBA image, edited in place)."""
    a = np.asarray(new).copy()
    found = stray(orig, new, boxes)
    for _, _, comp in found:
        a[comp] = 0
    if found:
        from PIL import Image
        new.paste(Image.fromarray(a))
    return len(found)


def _selftest():
    from PIL import Image, ImageDraw
    orig = Image.new("RGBA", (40, 20))
    ImageDraw.Draw(orig).rectangle((5, 2, 30, 17), fill=(255, 255, 255, 255))  # a "glyph"
    tight = orig.copy()
    ImageDraw.Draw(tight).rectangle((5, 4, 30, 17), fill=(0, 0, 0, 0))  # box misses the top 2 rows
    assert [s[:2] for s in stray(orig, tight)] == [(52, (5, 2, 30, 3))], stray(orig, tight)
    assert stray(orig, tight, [(5, 2, 26, 2)]) == []  # inside a box: may be English, left alone
    assert sweep(orig, tight, [(5, 4, 26, 14)]) == 1 and stray(orig, tight) == []
    whole = orig.copy()
    ImageDraw.Draw(whole).rectangle((5, 2, 30, 17), fill=(0, 0, 0, 0))
    assert stray(orig, whole) == []


def main(labels):
    import gen_gfx
    import sprite
    rs = gen_gfx.rows()
    bad = 0
    for lab in labels or rs:
        boxes = [r[0] for r in rs[lab]]
        for k, box, _ in stray(sprite.image(lab), gen_gfx.english(lab, rs[lab]), boxes):
            print(f"{lab}\t{k} px\t{box}")
            bad += 1
    print(f"leftover: {bad} blobs", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    _selftest()
    sys.exit(main(sys.argv[1:]))
