"""ITOC-only CRI CPK reader (Data.cpk has numeric file IDs and no names; tools/cpk.py refuses these).
usage: itoc.py x CPK OUTDIR   -> OUTDIR/<id>.<ext> plus index.tsv
Library: read_entries(path) -> [(id, off, csize, size)];  crilayla_decompress(bytes) -> bytes"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cpk import Utf


def read_entries(path):
    with open(path, "rb") as f:
        info = Utf(f.read(0x800), 16).rows[0]
        f.seek(info["ItocOffset"])
        tb = f.read(info["ItocSize"])
    assert tb[:4] == b"ITOC", tb[:4]
    t = Utf(tb, 16).rows[0]
    ents = []
    for key, fmt in (("DataL", ">HHH"), ("DataH", ">HII")):
        cell = t.get(key)
        if not cell or not cell[2]:
            continue
        rows = Utf(tb, cell[1]).rows
        ents += [(r["ID"], r["FileSize"], r["ExtractSize"]) for r in rows]
    ents.sort()
    align, off, out = info["Align"], info["ContentOffset"], []
    for fid, csize, size in ents:  # files sit in ID order, each padded to Align
        out.append((fid, off, csize, size))
        off += -(-csize // align) * align
    return out


def crilayla_decompress(b):
    assert b[:8] == b"CRILAYLA", b[:8]
    usize, hdr = struct.unpack_from("<II", b, 8)
    out = bytearray(usize + 0x100)
    out[:0x100] = b[hdr + 0x10:hdr + 0x110]
    pos, bitpool, bits = hdr + 0x10 - 1, 0, 0

    def get(n):
        nonlocal pos, bitpool, bits
        v = 0
        while n:
            if not bits:
                bitpool, bits = b[pos], 8
                pos -= 1
            take = min(n, bits)
            v = (v << take) | ((bitpool >> (bits - take)) & ((1 << take) - 1))
            bits -= take
            n -= take
        return v

    w = usize + 0x100 - 1  # data is written back to front
    end = 0x100
    while w >= end:
        if get(1):
            off = get(13) + 3
            n = 3
            for lv in (2, 3, 5, 8):
                v = get(lv)
                n += v
                if v != (1 << lv) - 1:
                    break
            else:
                while True:
                    v = get(8)
                    n += v
                    if v != 255:
                        break
            for _ in range(n):
                out[w] = out[w + off]
                w -= 1
        else:
            out[w] = get(8)
            w -= 1
    return bytes(out)


def sniff(d):
    for magic, ext in ((b"MIG.", "gim"), (b"PSMF", "pmf"), (b"RIFF", "at3"), (b"\x89PNG", "png"), (b"PTF", "ptf"),
                       (b"@UTF", "utf"), (b"PMF", "pmf"), (b"PK", "zip"), (b"CPK ", "cpk"), (b"\x7fELF", "elf")):
        if d.startswith(magic):
            return ext
    return "bin"


if __name__ == "__main__":
    cmd, path, out = sys.argv[1:4]
    assert cmd == "x"
    Path(out).mkdir(parents=True, exist_ok=True)
    with open(path, "rb") as f, open(Path(out) / "index.tsv", "w", encoding="utf-8") as ix:
        for fid, off, csize, size in read_entries(path):
            f.seek(off)
            d = f.read(csize)
            comp = d[:8] == b"CRILAYLA"
            if comp:
                d = crilayla_decompress(d)
            assert len(d) == size, (fid, len(d), size)
            ext = sniff(d)
            (Path(out) / f"{fid:05d}.{ext}").write_bytes(d)
            ix.write(f"{fid}\t{off}\t{csize}\t{size}\t{int(comp)}\t{ext}\t{d[:16].hex()}\n")
