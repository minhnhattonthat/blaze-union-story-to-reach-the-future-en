"""English sprites from data/gfx.tsv: each row clears one box of a sprite and draws its English there.
Row: label (sweep label, <file id>@<hex>), box x,y,w,h, style (STYLES below), Japanese (a note), English.
A label may have many rows: atlases hold many labels, and the game cuts each from its own rect, so English stays inside
the box the Japanese had. Every copy of a sprite's bytes in the archive gets the same edit (gfx.copies).
usage: gen_gfx.py preview [LABEL..]   -> work/gfx/<label>.png, original above, English below
       gen_gfx.py boxes LABEL..       -> ink boxes (x,y,w,h) per line segment, to write rows from
library: edits() -> {file id: bytes}, log lines in build/gfx.txt"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import gfx
import sprite

ROOT = Path(__file__).resolve().parents[1]
TSV = ROOT / "data/gfx.tsv"
FONTS = ROOT / "fonts"
OUT = ROOT / "work/gfx"

# fill: colour, or "rows" = each row takes the mean colour of the Japanese fill in that row (keeps gradients).
# stroke: (width, colour) or (width, "rows-dark"). clear: "alpha" (transparent) or "bg" (box border's commonest colour).
STYLES = {
    "banner": dict(font="SourceSans3-Black.ttf", fill="rows", stroke=(2, "dark"), clear="alpha", align="c"),
    "banner-l": dict(font="SourceSans3-Black.ttf", fill="rows", stroke=(2, "dark"), clear="alpha", align="l"),
    "banner-r": dict(font="SourceSans3-Black.ttf", fill="rows", stroke=(2, "dark"), clear="alpha", align="r"),
    "vbanner": dict(font="SourceSans3-Black.ttf", fill="rows", stroke=(2, "dark"), clear="alpha", align="c", rot=True),
    "menu": dict(font="SourceSans3-Bold.ttf", fill="rows", stroke=(1, "dark"), clear="alpha", align="l"),
    "menu-c": dict(font="SourceSans3-Bold.ttf", fill="rows", stroke=(1, "dark"), clear="alpha", align="c"),
    "label": dict(font="SourceSans3-Bold.ttf", fill="rows", stroke=None, clear="alpha", align="l"),
    "panel": dict(font="SourceSans3-Bold.ttf", fill="rows", stroke=None, clear="bg", align="l"),
    "panel-c": dict(font="SourceSans3-Bold.ttf", fill="rows", stroke=None, clear="bg", align="c"),
    "panel-r": dict(font="SourceSans3-Bold.ttf", fill="rows", stroke=None, clear="bg", align="r"),
    "panel-w": dict(font="SourceSans3-Bold.ttf", fill=(255, 255, 255), stroke=None, clear="bg", align="c"),
    "panel-y": dict(font="SourceSans3-Bold.ttf", fill=(255, 255, 0), stroke=None, clear="bg", align="c"),
    "paper": dict(font="SourceSans3-Bold.ttf", fill=(0, 0, 0), stroke=None, clear=(253, 252, 252, 255), align="c"),
    "menu-r": dict(font="SourceSans3-Bold.ttf", fill="rows", stroke=(1, "dark"), clear="alpha", align="r"),
    "note": dict(font="SourceSans3-Bold.ttf", fill="rows", stroke=(1, "dark"), clear="alpha", align="l", wrap=True, max=15),
    # text over art: "art" with EN "-" smears the art over the Japanese box, then "over" draws in a box of its own
    "art": dict(font="SourceSans3-Black.ttf", fill=(255, 255, 255), stroke=(2, (16, 16, 32)), clear="inpaint", align="l"),
    "mirror": dict(font="SourceSans3-Black.ttf", fill=(255, 255, 255), stroke=(2, (16, 16, 32)), clear="mirror", align="l"),
    "over": dict(font="SourceSans3-Black.ttf", fill=(255, 255, 255), stroke=(2, (16, 16, 32)), clear=None, align="l"),
    "over-c": dict(font="SourceSans3-Black.ttf", fill=(255, 255, 255), stroke=(2, (16, 16, 32)), clear=None, align="c"),
    "title": dict(font="SourceSans3-Black.ttf", fill=(255, 255, 255), stroke=(3, (0, 0, 0)), clear="alpha", align="l"),
    "stripe": dict(font="SourceSans3-Black.ttf", fill=(252, 254, 186), stroke=(2, (31, 27, 38)), clear="stripe", align="c"),
    "over1": dict(font="SourceSans3-Bold.ttf", fill=(255, 255, 255), stroke=(1, (16, 16, 32)), clear=None, align="l"),
    "panel-k": dict(font="SourceSans3-Bold.ttf", fill=(255, 255, 255), stroke=None, clear=(0, 0, 0, 255), align="c"),
    "pic-red": dict(font="SourceSans3-Bold.ttf", fill=(200, 30, 60), stroke=(1, (255, 255, 255)), clear=None, align="l", max=15),
    "pic-cream": dict(font="SourceSans3-Bold.ttf", fill=(245, 230, 170), stroke=(1, (60, 30, 20)), clear=None, align="l", max=14),
    # tutorial captions, yellow or white over art or bare alpha: bright lettering is inpainted, English drawn in place
    "cap": dict(font="SourceSans3-Bold.ttf", fill=(255, 236, 96), stroke=(2, (0, 0, 0)), clear="ink", align="c", max=14),
    "cap-w": dict(font="SourceSans3-Bold.ttf", fill=(255, 255, 255), stroke=(2, (0, 0, 0)), clear="ink", align="c", max=18),
    "cardcap": dict(font="SourceSans3-Bold.ttf", fill=(255, 255, 255), stroke=(2, (0, 0, 0)), clear="alpha", align="c", max=20),
    "tag": dict(font="SourceSans3-Bold.ttf", fill=(255, 240, 210), stroke=(1, (40, 30, 20)), clear="ink", align="l", max=10),
    # credit blocks: one row per text line; the small line sizes keep long names narrow in their fixed canvases
    "credit": dict(font="SourceSans3-Bold.ttf", fill="rows", stroke=(1, "dark"), clear="alpha", align="r", max=14),
    "credit-role": dict(font="SourceSans3-Bold.ttf", fill="rows", stroke=(1, "dark"), clear="alpha", align="r", max=12),
    # recap narration: whole page in one box, word-wrapped at the largest size that fits; "\n" ends a paragraph
    "page": dict(font="SourceSans3-Bold.ttf", fill=(255, 255, 255), stroke=(1, (24, 24, 40)), clear="alpha", align="c",
                 wrap=True, max=17),
    # recap diagram words over a gradient pill: the lettering (outline, halo, fill) is inpainted from the pill around
    # it, then English is drawn white-to-pill-colour with a black outline and a white halo, as the Japanese
    "pill": dict(font="SourceSans3-Black.ttf", fill="pill", stroke=(2, (8, 8, 16)), clear="pill", align="c", halo=True),
}
MIN_X = 0.62  # narrowest horizontal squeeze before the size shrinks instead


def rows():
    out = {}
    for n, line in enumerate(TSV.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split("\t")
        assert len(f) == 5, f"{TSV.name}:{n}: {len(f)} fields"
        lab, box, style, jp, en = f
        assert style in STYLES, f"{TSV.name}:{n}: style {style}"
        en = "" if en == "-" else en.replace("\\n", "\n")  # "-": clear the box, draw nothing
        out.setdefault(lab, []).append((tuple(map(int, box.split(","))), style, jp, en))
    return out


def lum(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]


def sample(crop):
    """-> (per-row fill colours, dark colour) of the original lettering in a box."""
    px = crop.load()
    w, h = crop.size
    ink = [px[x, y] for y in range(h) for x in range(w) if px[x, y][3] > 100]
    if not ink:
        return [(255, 255, 255)] * h, (0, 0, 0)
    ls = sorted(lum(p) for p in ink)
    cut = (ls[len(ls) // 10] + ls[-1 - len(ls) // 10]) / 2
    dark = [p for p in ink if lum(p) < cut] or ink
    dark = tuple(sorted(dark, key=lum)[len(dark) // 4][:3])
    fills = []
    for y in range(h):
        r = [px[x, y] for x in range(w) if px[x, y][3] > 100 and lum(px[x, y]) >= cut]
        fills.append(tuple(sum(c[i] for c in r) // len(r) for i in range(3)) if r else None)
    known = [i for i, c in enumerate(fills) if c]
    if not known:
        fills = [tuple(sorted(ink, key=lum)[-1][:3])] * h
    else:
        fills = [fills[min(known, key=lambda k: abs(k - y))] for y in range(h)]
    return fills, dark


def border_colour(img, box):
    x, y, w, h = box
    px = img.load()
    from collections import Counter
    c = Counter()
    for i in range(x - 1, x + w + 1):
        for j in (y - 1, y + h):
            if 0 <= i < img.width and 0 <= j < img.height:
                c[px[i, j]] += 1
    for j in range(y, y + h):
        for i in (x - 1, x + w):
            if 0 <= i < img.width and 0 <= j < img.height:
                c[px[i, j]] += 1
    return c.most_common(1)[0][0] if c else (0, 0, 0, 0)


def wrap(text, width, w):
    """Greedy word wrap of each paragraph ("\n"-separated) to w; a blank line between paragraphs."""
    out = []
    for para in text.split("\n"):
        line = ""
        for word in para.split():
            t = f"{line} {word}".strip()
            if line and width(t) > w:
                out.append(line)
                t = word
            line = t
        out += [line, ""]
    return out[:-1]


def text_layer(text, st, w, h):
    """White-on-black-stroke lettering fitted into w x h (ink box), squeezed before shrunk. -> L-mode luma, alpha."""
    sw = st["stroke"][0] if st["stroke"] else 0
    path = str(FONTS / st["font"])
    lines = text.split("\n")
    for px in range(min(h * 2, st.get("max", h * 2)), 5, -1):
        f = ImageFont.truetype(path, px)
        d = ImageDraw.Draw(Image.new("L", (1, 1)))
        if st.get("wrap"):
            lines = wrap(text, lambda s: d.textlength(s, font=f) + 2 * sw, w)
        bbs = [d.textbbox((0, 0), ln, font=f, stroke_width=sw) for ln in lines]
        ref = d.textbbox((0, 0), "Ag", font=f, stroke_width=sw)  # one size per box height, descender or not
        bbs = [(b[0], ref[1], b[2], ref[3]) for b in bbs]
        lh = ref[3] - ref[1]
        pitch = f.getmetrics()[0] + f.getmetrics()[1] if len(lines) > 1 else lh
        th = pitch * (len(lines) - 1) + lh
        tw = max(b[2] - b[0] for b in bbs)
        if th <= h and tw * (1 if st.get("wrap") else MIN_X) <= w:
            break
    top = min(b[1] for b in bbs)
    lay = Image.new("RGBA", (tw + 2, th + 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i, (ln, b) in enumerate(zip(lines, bbs)):
        x = {"l": 0, "c": (tw - (b[2] - b[0])) // 2, "r": tw - (b[2] - b[0])}[st["align"]] - b[0]
        d.text((x + 1, i * pitch - top + 1), ln, font=f, fill=(255, 255, 255, 255), stroke_width=sw,
               stroke_fill=(0, 0, 0, 255))
    bb = lay.getbbox() or (0, 0, 1, 1)
    lay = lay.crop((bb[0], 0, bb[2], lay.height))
    if lay.width > w:
        lay = lay.resize((w, lay.height), Image.LANCZOS)
    return lay


def draw(img, box, style, en, s=1.0):
    """s < 1 draws the English smaller than the box (fitted(): a packed group with no room for more ink)."""
    st = STYLES[style]
    x, y, w, h = box
    fills, dark = sample(img.crop((x, y, x + w, y + h)))
    if st["clear"] == "bg":
        # lettering on an opaque panel: ink is what differs from the panel, its darker part is the letter colour
        bgc = border_colour(img, box)
        ink = sorted((p for p in img.crop((x, y, x + w, y + h)).getdata()
                      if sum((a - b) ** 2 for a, b in zip(p[:3], bgc[:3])) > 3600), key=lum)
        ink = ink[:max(1, len(ink) * 2 // 5)] or [(0, 0, 0, 255)]
        dark = tuple(sum(p[i] for p in ink) // len(ink) for i in range(3))
        fills = [dark] * h
        img.paste(Image.new("RGBA", (w, h), bgc), (x, y))
    elif isinstance(st["clear"], tuple):
        img.paste(Image.new("RGBA", (w, h), st["clear"]), (x, y))
    elif st["clear"] == "inpaint":
        inpaint(img, box)
    elif st["clear"] == "ink":
        inpaint(img, box, yellow=True)
    elif st["clear"] == "pill":
        import numpy as np
        a = np.array(img.crop((x, y, x + w, y + h))).astype(int)
        sat = (a[..., :3].max(axis=2) - a[..., :3].min(axis=2) > 90) & (a[..., 3] > 200)
        pc = tuple(int(v) for v in a[sat][:, :3].mean(axis=0)) if sat.any() else (60, 90, 255)
        fills, dark = [tuple(int(255 + (pc[k] - 255) * j / max(h - 1, 1)) for k in range(3)) for j in range(h)], \
            st["stroke"][1]
        inpaint(img, box, letters=True)
    elif st["clear"] == "mirror":  # symmetric art (terrain diamonds): the box takes the mirror of the other side
        img.paste(img.crop((img.width - x - w, y, img.width - x, y + h)).transpose(Image.FLIP_LEFT_RIGHT), (x, y))
    elif st["clear"] == "alpha":
        img.paste(Image.new("RGBA", (w, h), (0, 0, 0, 0)), (x, y))
    elif st["clear"] == "stripe":  # lettering over a white bar: clear, then redraw each row's bar from its visible ends
        px = img.load()
        for j in range(y, y + h):
            xs = [i for i in range(x, x + w) if px[i, j][3] > 200 and min(px[i, j][:3]) > 245]
            for i in range(x, x + w):
                px[i, j] = (253, 252, 252, 255) if len(xs) > w // 4 and xs[0] <= i <= xs[-1] else (0, 0, 0, 0)
    if isinstance(st["fill"], tuple):
        fills, dark = [st["fill"]] * h, st["stroke"][1] if st["stroke"] else (0, 0, 0)
    if not en:
        return
    hw = 2 if st.get("halo") else 0
    tw, th = max(int(w * s) - hw, 1), max(int(h * s) - hw, 6)
    if st.get("rot"):  # vertical Japanese: English reads top to bottom, turned 90 degrees clockwise
        lay = text_layer(en, st, th, tw).transpose(Image.ROTATE_270)
    else:
        lay = text_layer(en, st, tw, th)
    ox =x + {"l": 0, "c": (w - lay.width) // 2, "r": w - lay.width}[st["align"]]
    oy = y if st.get("rot") else y + (h - lay.height) // 2  # vertical titles hang from the top, as the Japanese
    halo = None
    if st.get("halo"):  # 1 px white ring outside the stroke
        from PIL import ImageFilter
        big = Image.new("RGBA", (lay.width + 2, lay.height + 2), (0, 0, 0, 0))
        big.paste(lay, (1, 1))
        lay, ox, oy = big, ox - 1, oy - 1
        halo = lay.split()[3].filter(ImageFilter.MaxFilter(3)).load()
    src = lay.load()
    dst = img.load()
    for j in range(lay.height):
        f = fills[min(max(oy + j - y, 0), h - 1)]
        for i in range(lay.width):
            r, g, b, a = src[i, j]
            white = halo is not None and not a and halo[i, j]
            if white:
                a = halo[i, j]
            if not a or not (y <= oy + j < min(y + h, img.height) and x <= ox + i < min(x + w, img.width)):
                continue
            t = r / 255
            c = (255, 255, 255) if white else tuple(int(dark[k] + (f[k] - dark[k]) * t) for k in range(3))
            bg = dst[ox + i, oy + j]
            al = a / 255
            dst[ox + i, oy + j] = tuple(int(c[k] * al + bg[k] * (1 - al)) for k in range(3)) + (max(a, bg[3]),)


def inpaint(img, box, letters=False, yellow=False, mask=None):
    """Remove white outlined lettering in box: mask its fill plus 3 px of outline, then fill the mask from what is
    around it (premultiplied RGBA, 4-neighbour mean), so art and transparency outside the letters stay.
    yellow=True (tutorial captions, white or yellow): the mask is the bright lettering in the box and the outline joined
    to it, up to 9 px past the box.
    letters=True (pill words, any fill colour): mask the black outline, the white halo and what they enclose, then
    snap the box's alpha to 0 or 255 (the fill blends transparency and pill at the pill's edge).
    mask(a) -> bool array: the lettering of an opaque image, grown 2 px."""
    import numpy as np
    x, y, w, h = box
    pad = 9 if yellow else 1  # rough caption boxes: the lettering may run past them
    X0, Y0, X1, Y1 = max(x - pad, 0), max(y - pad, 0), min(x + w + pad, img.width), min(y + h + pad, img.height)
    a = np.array(img.crop((X0, Y0, X1, Y1))).astype(float)
    inbox = np.zeros(a.shape[:2], bool)
    inbox[y - Y0:y - Y0 + h, x - X0:x - X0 + w] = True
    if mask:
        from scipy import ndimage as ndi
        m = ndi.binary_dilation(mask(a) & inbox, iterations=2) & inbox
    elif yellow:  # the lettering is the bright fill in the box plus all bright or black ink joined to it
        from scipy import ndimage as ndi
        op = a[..., 3] > 60
        bright = (a[..., :2].min(axis=2) > 170) & op
        m = ndi.binary_propagation(bright & inbox, ndi.generate_binary_structure(2, 2),
                                   mask=(bright | (a[..., :3].max(axis=2) < 70)) & op)
        inbox[:] = True  # the mask, not the box, bounds the fill now
        m = ndi.binary_dilation(m, iterations=1) & (a[..., 3] > 0)
        m |= ndi.binary_dilation(m, iterations=3) & (a[..., 3] > 0) & ~op  # the faint fringe would seed the fill
    elif letters:
        from scipy import ndimage as ndi
        rgb, op = a[..., :3], a[..., 3] > 60
        # the pill is the saturated colour that reaches outside the box; every other opaque pixel in it is lettering
        sat = (rgb.max(axis=2) - rgb.min(axis=2) > 90) & op
        lab, _ = ndi.label(sat)
        pill = np.isin(lab, np.unique(lab[sat & ~inbox]))
        m = op & inbox & ~pill
        m = ndi.binary_dilation(m, iterations=1) & inbox & (a[..., 3] > 0)  # clear pixels stay clear: no new ink
    else:
        m = (a[..., :3].min(axis=2) > 170) & (a[..., 3] > 60) & inbox
        for _ in range(3):
            g = m.copy()
            g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
            m = g & inbox
    a[..., :3] *= a[..., 3:] / 255
    known = ~m
    while not known.all():
        acc, n = np.zeros(a.shape), np.zeros(known.shape)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = np.roll(known, (dy, dx), (0, 1))
            acc += np.roll(a, (dy, dx), (0, 1)) * k[..., None]
            n += k
        new = ~known & (n > 0)
        a[new] = acc[new] / n[new][:, None]
        known |= new
    if letters:  # the peel above streaks along its fronts over wide masks: smooth toward the harmonic fill
        for _ in range(80):
            s = sum(np.roll(a, d, (0, 1)) for d in ((1, 0), (-1, 0), (0, 1), (0, -1))) / 4
            a[m] = s[m]
    al = a[..., 3:]
    a[..., :3] = np.where(al > 0, a[..., :3] * 255 / np.maximum(al, 1e-6), 0)
    if letters:
        # pills are convex: under the letters the fill's edge cuts inside them, so lean to transparent
        a[..., 3] = np.where(m, np.where(a[..., 3] >= 200, 255, 0), a[..., 3])
    if yellow:  # specks the fill left on bare alpha; a blob touching the crop's edge may be art, so it stays
        lab, n = ndi.label(a[..., 3] > 0)
        size = ndi.sum(np.ones(lab.shape), lab, range(1, n + 1))
        edge = set(lab[0]) | set(lab[-1]) | set(lab[:, 0]) | set(lab[:, -1])
        a[np.isin(lab, [i + 1 for i in range(n) if size[i] < 80 and i + 1 not in edge])] = 0
    img.paste(Image.fromarray(a.round().clip(0, 255).astype("uint8")), (X0, Y0))


def english(label, items, s=1.0):
    img = sprite.image(label).copy()
    for box, style, jp, en in items:
        draw(img, box, style, en, s)
    return img


def _bright(a):
    return a[..., :3].mean(axis=2) > 140


def _red(a):
    return a[..., 0] - a[..., 1] > 35


PIC1 = [  # box, what marks the lettering, style, English: the XMB background, an opaque 480x272 PNG off the disc
    ((199, 126, 200, 17), _red, "pic-red", "Tactical Fantasy RPG"),
    ((150, 188, 322, 16), _bright, "pic-cream", "Warriors racing across an empire under dark clouds"),
    ((198, 209, 280, 15), _bright, "over1", "Form up with allies in the Union System!"),
    ((198, 224, 280, 15), _bright, "over1", "Wield Tactics Cards to turn the tide of war,"),
    ((198, 239, 280, 15), _bright, "over1", "choose your future and carve it out!!"),
]


def pic1(png):
    """English PIC1.PNG from the disc's own bytes."""
    import io
    img = Image.open(io.BytesIO(png)).convert("RGBA")
    for box, mask, style, en in PIC1:
        inpaint(img, box, mask=mask)
        draw(img, box, style, en)
    out = io.BytesIO()
    img.convert("RGB").save(out, "PNG", optimize=True)
    return out.getvalue()


GROWN = set()  # labels whose group got a new slice at the end of its PTP file (gfx.grow)


def fitted(label, items):
    """-> (image, scale): the largest English (scale 1 down to 0.5) whose ink the group's slices and cells can hold.
    In a PTP file, English that would drop under 85% gets a bigger slice instead, if every copy is in a PTP file."""
    d, kind, off = sprite.load(label)
    err = None
    for s in (1, .92, .85, .78, .7, .62, .55, .5):
        img = english(label, items, s)
        if kind != "ptg":
            return img, s
        if s < .85 and d[:4] == b"PTP\0":
            a, b = gfx.span(d, off)
            if all((gfx.CPK / f"{fid:05d}.bin").open("rb").read(4) == b"PTP\0" for fid, _ in gfx.copies(d[a:b])):
                big = english(label, items)
                try:
                    gfx.repack(bytearray(d), off, big, pal=gfx.group_palette(d, off), grown=True)
                    GROWN.add(label)
                    return big, 1
                except ValueError:
                    pass  # past the two slices a grown group may have: shrink as usual
        try:
            gfx.repack(bytearray(d), off, img, pal=gfx.group_palette(d, off))
            return img, s
        except ValueError as e:
            err = e
    raise ValueError(f"{label}: {err}")


def edits(log=ROOT / "build/gfx.txt"):
    """{file id: edited bytes} for every sprite in data/gfx.tsv and each copy of its bytes."""
    files = {}
    lines = []
    for label, items in rows().items():
        img, s = fitted(label, items)
        d, kind, off = sprite.load(label)
        a, b = gfx.span(d, off) if kind == "ptg" else (off, off + gfx.ptx_size(d, off))
        pal = gfx.group_palette(d, off) if kind == "ptg" else sprite.palette_at(d, off)
        for fid, o in gfx.copies(d[a:b]):
            buf = files.setdefault(fid, bytearray((gfx.CPK / f"{fid:05d}.bin").read_bytes()))
            at = o + (off - a)
            if kind == "ptg":
                gfx.repack(buf, at, img, pal=pal, grown=label in GROWN)
            else:
                gfx.write_ptx(buf, at, img, pal=pal)
            lines.append(f"{fid}@{at:x}\t{label}\n")
    log.parent.mkdir(exist_ok=True)
    log.write_text("".join(lines), encoding="utf-8", newline="\n")
    return {k: bytes(v) for k, v in files.items()}


def boxes(label, gap=6):
    img = sprite.image(label)
    a = img.split()[3].load()
    W, H = img.size
    on = [any(a[x, y] > 0 for x in range(W)) for y in range(H)]
    y = 0
    while y < H:
        if not on[y]:
            y += 1
            continue
        y0 = y
        while y < H and on[y]:
            y += 1
        cols = [any(a[x, j] > 0 for j in range(y0, y)) for x in range(W)]
        x = 0
        while x < W:
            if not cols[x]:
                x += 1
                continue
            x0, g = x, 0
            while x < W and g < gap:
                g = 0 if cols[x] else g + 1
                x += 1
            print(f"{label}\t{x0},{y0},{x - g - x0},{y - y0}")


def preview(labels):
    OUT.mkdir(parents=True, exist_ok=True)
    rs = rows()
    for label in labels or rs:
        old = sprite.image(label)
        new, s = fitted(label, rs[label]) if label in rs else (old, 1)
        if s < 1:
            print(f"{label}: English drawn at {s:.0%} to fit the group")
        d, kind, off = sprite.load(label)
        new = gfx.snapped(new, gfx.group_palette(d, off) if kind == "ptg" else sprite.palette_at(d, off))
        sheet = Image.new("RGBA", (old.width, old.height * 2 + 4), (70, 70, 110, 255))
        sheet.alpha_composite(old, (0, 0))
        sheet.alpha_composite(new, (0, old.height + 4))
        sheet.save(OUT / f"{label.replace('@', '_')}.png")
        print(OUT / f"{label.replace('@', '_')}.png")


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "boxes":  # boxes LABEL.. [--gap N]: smaller gap splits words
        gap = int(args.pop(args.index("--gap") + 1)) if "--gap" in args else 6
        for lab in [a for a in args if a != "--gap"]:
            boxes(lab, gap)
    elif cmd == "preview":
        preview(args)
