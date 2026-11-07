"""Draw sprites by their sweep label (<file id>@<hex first-slice offset>, as in work/sweep/index.tsv) to PNGs, whole:
a group through ptg.render, a lone PTX as is.
usage: sprite.py OUTDIR LABEL.. [--zoom N]; library: load(label) -> (file bytes, kind, offset), image(label) -> RGBA"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gfx
import ptg
import ptx

_cache = {}


def load(label):
    fid, off = label.split("@")
    fid, off = int(fid), int(off, 16)
    if fid not in _cache:
        d = (gfx.CPK / f"{fid:05d}.bin").read_bytes()
        _cache[fid] = (d, gfx.sprites(d))
    d, sp = _cache[fid]
    kind, o = sp[off]
    return d, kind, o


def palette_at(d, off):
    if ptx.parse(d, off)["fmt"] == 3:  # direct colour
        return None
    o, pal = off, ptx.palette(d, off)
    while pal is None:
        o = d.rfind(b"PTX@", 0, o)
        pal = ptx.palette(d, o)
    return pal


def image(label):
    d, kind, o = load(label)
    if kind == "ptg":
        return ptg.render(d, o, pal=gfx.group_palette(d, o))
    return ptx.decode(d, o, pal=palette_at(d, o))


if __name__ == "__main__":
    from PIL import Image
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    zoom = int(sys.argv[sys.argv.index("--zoom") + 1]) if "--zoom" in sys.argv else 1
    for lab in [a for a in sys.argv[2:] if "@" in a]:
        img = image(lab)
        if zoom > 1:
            img = img.resize((img.width * zoom, img.height * zoom), Image.NEAREST)
        bg = Image.new("RGBA", img.size, (70, 70, 110, 255))
        bg.alpha_composite(img)
        bg.save(out / f"{lab.replace('@', '_')}.png")
        print(lab, img.size)
