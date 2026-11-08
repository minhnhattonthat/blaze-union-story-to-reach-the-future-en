"""Yggdra Union (USA), same engine, official English: read its sprites straight from the ISO for data/gfx.tsv rows of
style `ygg` (English column = Yggdra label <afs entry>@<hex first-slice offset>, as in tools/sprite.py).
data0.afs: "AFS\\0", u32 count, count x (u32 offset, u32 size). An entry starting "ZLB\\0" is u32 raw size + zlib.
usage: ygg.py OUTDIR LABEL..  (draws Yggdra sprites to PNGs); library: image(label) -> RGBA"""
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gfx
import iso9660
import ptg
import ptx
import sprite

ROOT = Path(__file__).resolve().parents[1]
ISO = ROOT / "rom/Yggdra Union - We'll Never Fight Alone (USA).iso"  # pinned in rom.sha1
AFS = "/PSP_GAME/USRDIR/Data/data0.afs"
_files = {}


def entry(n):
    if n not in _files:
        with open(ISO, "rb") as f:
            lba = next(lba for p, lba, _, _ in iso9660.listing(f) if p == AFS)
            f.seek(lba * 2048)
            assert f.read(4) == b"AFS\0"
            f.seek(lba * 2048 + 8 + 8 * n)
            off, size = struct.unpack("<II", f.read(8))
            f.seek(lba * 2048 + off)
            d = f.read(size)
        if d[:4] == b"ZLB\0":
            raw = struct.unpack_from("<I", d, 4)[0]
            d = zlib.decompress(d[8:])
            assert len(d) == raw, (n, len(d), raw)
        _files[n] = (d, gfx.sprites(d))
    return _files[n]


def image(label):
    n, off = label.split("@")
    d, sp = entry(int(n))
    kind, o = sp[int(off, 16)]
    if kind == "ptg":
        return ptg.render(d, o, pal=gfx.group_palette(d, o))
    return ptx.decode(d, o, pal=sprite.palette_at(d, o))


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for lab in sys.argv[2:]:
        img = image(lab)
        img.save(out / f"ygg_{lab.replace('@', '_')}.png")
        print(lab, img.size)
