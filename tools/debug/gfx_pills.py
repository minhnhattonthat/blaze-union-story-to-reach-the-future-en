"""Find the white, black-outlined lettering on the coloured pills of the recap diagrams (1532-1577, 240x100).
usage: gfx_pills.py OUT.png LABEL..  -> prints LABEL<TAB>n<TAB>x,y,w,h per lettering box, and draws the numbered
boxes on a sheet (OUT.png) to read which word each box holds."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sprite


def grow(m, r):
    for _ in range(r):
        g = m.copy()
        g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
        m = g
    return m


def boxes(img):
    a = np.array(img).astype(int)
    rgb, al = a[..., :3], a[..., 3] > 200
    white = (rgb.min(axis=2) >= 200) & al
    black = (rgb.max(axis=2) < 60) & al
    pill = ((rgb.max(axis=2) - rgb.min(axis=2)) > 90) & al
    m = white & grow(black, 2) & grow(pill, 10)
    lab = np.zeros(m.shape, int)
    out, H, W = [], *m.shape
    g = grow(m, 4)
    n = 0
    for y0, x0 in zip(*np.nonzero(g)):
        if lab[y0, x0]:
            continue
        n += 1
        st, pts = [(y0, x0)], []
        lab[y0, x0] = n
        while st:
            y, x = st.pop()
            pts.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                j, i = y + dy, x + dx
                if 0 <= j < H and 0 <= i < W and g[j, i] and not lab[j, i]:
                    lab[j, i] = n
                    st.append((j, i))
        ys, xs = zip(*pts)
        X0, Y0, X1, Y1 = min(xs), min(ys), max(xs) + 1, max(ys) + 1
        fill = m[Y0:Y1, X0:X1].mean()
        if X1 - X0 >= 14 and Y1 - Y0 >= 12 and fill > 0.12:
            out.append((X0, Y0, X1 - X0, Y1 - Y0))
    return sorted(out, key=lambda b: (b[1], b[0]))


if __name__ == "__main__":
    dst, labels = sys.argv[1], sys.argv[2:]
    tiles = []
    for lab in labels:
        img = sprite.image(lab)
        t = img.copy()
        d = ImageDraw.Draw(t)
        for k, (x, y, w, h) in enumerate(boxes(img), 1):
            print(f"{lab}\t{k}\t{x},{y},{w},{h}")
            d.rectangle((x, y, x + w - 1, y + h - 1), outline=(0, 255, 0, 255))
            d.text((x + 1, y + 1), str(k), fill=(255, 255, 0, 255))
        d.text((2, 2), lab, fill=(255, 255, 0, 255))
        tiles.append(t)
    cols = 3
    W, H = max(t.width for t in tiles), max(t.height for t in tiles)
    sheet = Image.new("RGBA", (W * cols, H * ((len(tiles) + cols - 1) // cols)), (70, 70, 110, 255))
    for i, t in enumerate(tiles):
        sheet.alpha_composite(t, ((i % cols) * W, (i // cols) * H))
    sheet.save(dst)
