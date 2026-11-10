"""After build.py: the built disc changes only what the build meant to change. Exit 1 if not.

    python -X utf8 tools/verify_build.py [ISO]

- EBOOT segment 0: every changed byte has a write in build/writes.txt, each write found the original bytes, none was overwritten (romdiff).
- Disc: every file but EBOOT.BIN and Data.cpk is byte-identical to the dump.
- Data.cpk: only the event scripts and file 3 (fonts, FCT text) differ.
"""
import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build
import elfpatch
import extract
import iso9660
import itoc
import romdiff

ROOT = build.ROOT


def check_eboot(new, log=ROOT / "build/writes.txt"):
    """Error lines for segment 0 of the built EBOOT against the dump."""
    orig = extract.ELF.read_bytes()
    size = struct.unpack_from("<I", orig, 0x34 + 16)[0]
    seg, out = orig[elfpatch.SEG0:elfpatch.SEG0 + size], new[elfpatch.SEG0:elfpatch.SEG0 + size]
    writes = romdiff.load_writes(str(log))
    errs, changed = romdiff.check(seg, out, set(), writes)
    print(f"EBOOT segment 0: {len(writes)} writes, {changed} bytes changed, {len(errs)} errors")
    return errs


def digests(iso):
    """{path: sha1} of every file on the disc."""
    out = {}
    with open(iso, "rb") as f:
        for name, lba, size, _ in iso9660.listing(f):
            f.seek(lba * 2048)
            out[name] = hashlib.sha1(f.read(size)).hexdigest()
    return out


def check_disc(iso):
    old, new = digests(build.ROM), digests(iso)
    errs = [f"{n}: {'missing' if n not in new else 'added' if n not in old else 'differs'}"
            for n in sorted(old.keys() | new.keys()) if n not in (build.EBOOT, build.CPK, build.PIC1) and old.get(n) != new.get(n)]
    print(f"disc: {len(old)} files, {len(errs)} unexpected differences")
    return errs


def check_cpk(iso):
    """Ids whose bytes differ between the unpacked dump and the built archive."""
    tmp = Path(iso).with_suffix(".verify.tmp")
    tmp.write_bytes(build.extract(iso, build.CPK))
    try:
        orig = ROOT / "work/iso/PSP_GAME/USRDIR/Data/Data.cpk"
        olds, news = ({e[0]: e[1:3] for e in itoc.read_entries(p)} for p in (orig, tmp))
        assert olds.keys() == news.keys(), "archive ids changed"
        art = ROOT / "build/gfx.txt"  # sprite files gen_gfx wrote, one "fid@offset<TAB>label" per sprite
        allowed = set(extract.EVENTS) | {3} | {int(ln.split("@")[0]) for ln in art.read_text().splitlines()}
        changed = set()
        with open(orig, "rb") as a, open(tmp, "rb") as b:
            for i, (off, size) in olds.items():
                a.seek(off)
                b.seek(news[i][0])
                if a.read(size) != b.read(news[i][1]):
                    changed.add(i)
        bad = sorted(changed - allowed)
    finally:
        tmp.unlink()
    print(f"Data.cpk: {len(olds)} files, {len(changed)} rebuilt, {len(bad)} outside events, file 3 and sprite files")
    return [f"Data.cpk {i} changed" for i in bad]


def main():
    iso = sys.argv[1] if len(sys.argv) > 1 else str(build.OUT)
    errs = check_eboot(build.extract(iso, build.EBOOT)) + check_disc(iso) + check_cpk(iso)
    print("\n".join(errs[:50]))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
