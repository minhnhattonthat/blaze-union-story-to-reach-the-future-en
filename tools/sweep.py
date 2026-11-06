"""Static graphics sweep: draw every sprite group (PTG@) whole, every other PTX@ as is, every top-level PNG and the PNGs
inside FCT 3 and on the disc, deduped by bytes, on numbered sheets with an index for the survey in docs/re/graphics.md.
Slices with no palette anywhere are drawn in grey and labelled so; nothing is skipped silently.
Up to 24 px tall: t*.png at 2x, label beside. Taller: s*.png at 1x, halved when wider than 256 or taller than 200.
usage: sweep.py work/cpk work/sweep [--extra FILE_OR_DIR]... [--min-id N] [--max-id N]"""
import hashlib
import re
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import ptg
from ptx import decode, palette, parse

PAGE_W, PAGE_H = 1440, 1000
BG = (70, 70, 110)
LABEL_W = 78  # "02700@1a2b3c" in PIL's default font
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
GREY = tuple(0xFF000000 | (v * 0x11) * 0x010101 for v in range(16)) + tuple(0xFF000000 | v * 0x010101 for v in range(16, 256))


def textures(d):
    for m in re.finditer(b"PTX@", d):
        o = m.start()
        try:
            h = parse(d, o)
        except struct.error:
            continue
        if not (0 < h["w"] <= 1024 and 0 < h["h"] <= 1024 and h["fmt"] in (4, 5) and 0 < h["npal"] <= 256):
            continue
        bpp = 8 if h["fmt"] == 5 else 4
        size = h["doff"] + h["stride"] * h["h"] * bpp // 8
        if o + size > len(d) + 64:
            continue
        yield o, h, size


def groups(d):
    """-> {offset: parsed PTG} for every group whose slices are all real PTX."""
    out = {}
    for m in re.finditer(b"PTG@", d):
        try:
            g = ptg.parse(d, m.start())
        except struct.error:
            continue
        if g["slices"] and all(d[s:s + 4] == b"PTX@" for s in g["slices"]):
            out[m.start()] = g
    return out


class Sheets:
    """Pages filled left to right in shelves."""

    def __init__(self, out, prefix, beside):
        self.out, self.prefix, self.beside = out, prefix, beside
        self.page, self.sheet, self.x, self.y, self.row = 0, None, 0, 0, 0

    def add(self, img, label, ix):
        if self.sheet is None:
            self._new()
        w = img.width + (LABEL_W if self.beside else 0) + 4
        h = max(img.height, 11) + (0 if self.beside else 11) + 2
        if self.x + w > PAGE_W:
            self.x, self.y, self.row = 0, self.y + self.row, 0
        if self.y + h > PAGE_H:
            self._new()
        self.draw.text((self.x, self.y), label, fill=(255, 255, 0))
        pos = (self.x + LABEL_W, self.y) if self.beside else (self.x, self.y + 11)
        self.sheet.paste(img, pos, img)
        self.x += w
        self.row = max(self.row, h)
        ix.write(f"{self.prefix}{self.page:03d}\t{label}\t{img.width}x{img.height}\n")

    def _new(self):
        self.flush()
        self.sheet = Image.new("RGB", (PAGE_W, PAGE_H), BG)
        self.draw = ImageDraw.Draw(self.sheet)
        self.x, self.y, self.row = 0, 0, 0

    def flush(self):
        if self.sheet:
            self.sheet.save(self.out / f"{self.prefix}{self.page:03d}.png")
            self.page += 1
            self.sheet = None


def main():
    args = sys.argv[1:]
    extras = [Path(args[i + 1]) for i, a in enumerate(args) if a == "--extra"]
    src, out = Path(args[0]), Path(args[1])
    lo = int(args[args.index("--min-id") + 1]) if "--min-id" in args else 0
    hi = int(args[args.index("--max-id") + 1]) if "--max-id" in args else 99999
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()
    seen, failed = set(), []
    stats = dict(groups=0, ptx=0, png=0, grey=0)
    small, big = Sheets(out, "t", True), Sheets(out, "s", False)

    def put(img, label, ix):
        if img.height <= 24:
            small.add(img.resize((img.width * 2, img.height * 2), Image.NEAREST), label, ix)
        else:
            if img.width > 256 or img.height > 200:
                img = img.resize((max(1, img.width // 2), max(1, img.height // 2)), Image.BILINEAR)
            big.add(img, label, ix)

    with open(out / "index.tsv", "w", encoding="utf-8") as ix:
        files = [p for p in sorted(src.iterdir()) if p.suffix in (".bin", ".png") and lo <= int(p.stem) <= hi]
        for e in extras:
            files += sorted(e.rglob("*.png")) if e.is_dir() else [e]
        for p in files:
            d = p.read_bytes()
            if d[:8] == PNG_MAGIC:
                k = hashlib.md5(d).hexdigest()
                if k not in seen:
                    seen.add(k)
                    stats["png"] += 1
                    put(Image.open(p).convert("RGBA"), p.stem if p.parent == src else f"{p.parent.name}/{p.stem}", ix)
                continue
            gs = groups(d)
            owned = {s: g for g in gs.values() for s in g["slices"]}
            pal = None
            # A group sits right before its slices, so walk slices and draw the group at its first one.
            for o, h, size in textures(d):
                pal = palette(d, o) or pal
                g = owned.get(o)
                tag = f"{p.stem}@{o:x}"
                try:
                    if g:
                        if g["slices"][0] != o:
                            continue
                        last = parse(d, g["slices"][-1])
                        end = g["slices"][-1] + last["doff"] + last["stride"] * last["h"] * (8 if last["fmt"] == 5 else 4) // 8
                        k = hashlib.md5(d[g["off"]:end]).hexdigest()
                        if k in seen:
                            continue
                        seen.add(k)
                        grey = pal is None
                        img = ptg.render(d, g["off"], pal=GREY if grey else pal)
                        stats["groups"] += 1
                    else:
                        k = hashlib.md5(d[o:o + size]).hexdigest()
                        if k in seen:
                            continue
                        seen.add(k)
                        grey = pal is None
                        img = decode(d, o, pal=GREY if grey else pal)
                        stats["ptx"] += 1
                    stats["grey"] += grey
                    put(img, tag + ("g" if grey else ""), ix)
                except Exception as e:
                    failed.append(f"{tag}: {e}")
    small.flush()
    big.flush()
    print(stats, f"t pages {small.page}, s pages {big.page}, failed {len(failed)}")
    for f in failed:
        print("failed", f)


if __name__ == "__main__":
    main()
