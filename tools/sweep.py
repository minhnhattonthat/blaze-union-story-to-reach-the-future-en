"""Static graphics sweep: find every PTX@ texture in the unpacked CPK by magic, dedupe by bytes, write numbered contact
sheets plus an index for the survey in docs/re/graphics.md. Prints every region skipped and why.
Strips (height <= 16, mostly pre-rendered text) go on their own sheets at 2x so they can be read; the rest on s*.png.
usage: sweep.py work/cpk work/sweep [--min-id N] [--max-id N]"""
import hashlib
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ptx import decode, palette, parse

CELL = (240, 136)
GRID = (6, 5)
STRIP_W, STRIP_ROWS = 720, 40
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


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


class Sheets:
    """Pages of cells, or (strip mode) rows of strips in two columns at 2x."""

    def __init__(self, out, prefix, strip):
        self.out, self.prefix, self.strip = out, prefix, strip
        self.n, self.page, self.sheet, self.draw = 0, 0, None, None
        self.per = STRIP_ROWS * 2 if strip else GRID[0] * GRID[1]

    def add(self, img, label, ix):
        from PIL import Image, ImageDraw
        if self.n % self.per == 0:
            self.flush()
            size = (STRIP_W * 2, STRIP_ROWS * 34) if self.strip else (GRID[0] * CELL[0], GRID[1] * (CELL[1] + 10))
            self.sheet = Image.new("RGB", size, (70, 70, 110))
            self.draw = ImageDraw.Draw(self.sheet)
        i = self.n % self.per
        if self.strip:
            cx, cy = (i // STRIP_ROWS) * STRIP_W, (i % STRIP_ROWS) * 34
            t = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
            self.draw.text((cx + 1, cy - 1), label, fill=(255, 255, 0))
            self.sheet.paste(t, (cx, cy + 10), t)
        else:
            cx, cy = i % GRID[0] * CELL[0], i // GRID[0] * (CELL[1] + 10)
            s = min(CELL[0] / img.width, CELL[1] / img.height, 1)
            t = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.NEAREST if s == 1 else Image.BILINEAR)
            self.sheet.paste(t, (cx, cy + 10), t)
            self.draw.text((cx + 1, cy - 1), label, fill=(255, 255, 0))
        ix.write(f"{self.prefix}{self.page:03d}\t{i}\t{label}\n")
        self.n += 1

    def flush(self):
        if self.sheet:
            self.sheet.save(self.out / f"{self.prefix}{self.page:03d}.png")
            self.page += 1
            self.sheet = None


def main():
    from PIL import Image
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    lo = int(sys.argv[sys.argv.index("--min-id") + 1]) if "--min-id" in sys.argv else 0
    hi = int(sys.argv[sys.argv.index("--max-id") + 1]) if "--max-id" in sys.argv else 99999
    out.mkdir(parents=True, exist_ok=True)
    seen, skipped = set(), []
    big, strips = Sheets(out, "s", False), Sheets(out, "t", True)
    with open(out / "index.tsv", "w", encoding="utf-8") as ix:
        for p in sorted(src.iterdir()):
            if p.suffix not in (".bin", ".png") or not (lo <= int(p.stem) <= hi):
                continue
            d = p.read_bytes()
            if d[:8] == PNG_MAGIC:
                k = hashlib.md5(d).hexdigest()
                if k not in seen:
                    seen.add(k)
                    img = Image.open(p).convert("RGBA")
                    big.add(img, f"{p.stem} png {img.width}x{img.height}", ix)
                continue
            pal = None
            for o, h, size in textures(d):
                pal = palette(d, o) or pal
                k = hashlib.md5(d[o:o + size]).hexdigest()
                if k in seen:
                    continue
                seen.add(k)
                try:
                    img = decode(d, o, pal=pal)
                except Exception as e:
                    skipped.append(f"{p.stem}@{o:#x}: {e}")
                    continue
                (strips if h["h"] <= 16 else big).add(img, f"{p.stem}@{o:x} {h['w']}x{h['h']}", ix)
    big.flush()
    strips.flush()
    print(f"unique {len(seen)}, s pages {big.page}, t pages {strips.page}, skipped {len(skipped)}")
    for s in skipped:
        print("skipped", s)


if __name__ == "__main__":
    main()
