"""Build build/blaze_union_en.iso from the pinned dump. usage: build.py [OUT]
With no edits the output is byte-identical to the original (tests/test_build.py). edits() is where later phases plug in."""
import hashlib
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_rom
import iso9660
import itoc

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom/Blaze Union - Story to Reach The Future (Japan).iso"
OUT = ROOT / "build/blaze_union_en.iso"
MARKER = ROOT / "build/blaze_union_marker.iso"
CPK = "/PSP_GAME/USRDIR/Data/Data.cpk"
EBOOT = "/PSP_GAME/SYSDIR/EBOOT.BIN"


def extract(iso, name):
    """Bytes of one file on the disc."""
    with open(iso, "rb") as f:
        _, lba, size, _ = next(e for e in iso9660.listing(f) if e[0] == name)
        f.seek(lba * 2048)
        return f.read(size)


def edits():
    """{Data.cpk file id: uncompressed bytes}. Nothing yet."""
    return {}


def build(out=OUT, repl=None, keep_same=True, eboot=None):
    """Write the ISO from the dump: Data.cpk rebuilt with repl, a bigger archive goes to the end of the image."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".cpk.tmp")  # itoc.rebuild reads a path
    tmp.write_bytes(extract(ROM, CPK))
    try:
        data = itoc.rebuild(tmp, edits() if repl is None else repl, keep_same)
    finally:
        tmp.unlink()
    files = {CPK: data}
    if eboot:
        files[EBOOT] = eboot
    iso9660.patch(str(ROM), str(out), files)
    return out


def build_marker(out=MARKER):
    """Every line replaced by [id] filler: docs/re/text.md, phase 5."""
    import insert
    import marker
    m = marker.Marker()
    repl, eboot, count = insert.build(m)
    m.save()
    print("marked", count, "strings; EBOOT", len(eboot))
    return build(out, repl=repl, keep_same=False, eboot=eboot)


if __name__ == "__main__":
    t = time.time()
    check_rom.check()
    if "--marker" in sys.argv:
        out = build_marker()
    else:
        out = build(sys.argv[1] if len(sys.argv) > 1 else OUT)
    with open(out, "rb") as f:
        print(out, out.stat().st_size, "sha1", hashlib.file_digest(f, "sha1").hexdigest(), f"{time.time() - t:.0f}s")
