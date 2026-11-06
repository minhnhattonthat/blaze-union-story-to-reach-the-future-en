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


def _table(name, cols, fmt, rows):
    """A @UTF table in the layout CRI's packer gives the two ITOC row tables (the identity test proves byte-exact)."""
    strs = b"<NULL>\0" + name + b"\0"
    head = b""
    for col, flag in cols:
        head += bytes([flag]) + struct.pack(">I", len(strs))
        strs += col + b"\0"
    rowlen = struct.calcsize(fmt)
    rows_off = 24 + len(head)
    body = head + b"".join(struct.pack(fmt, *r) for r in rows) + strs
    size = -(-(24 + len(body) + 8) // 8) * 8 - 8  # size field leaves out its 8-byte tag; the table ends 8-aligned
    return b"@UTF" + struct.pack(">IIIIIHHI", size, rows_off, rows_off + len(rows) * rowlen, size, 7, len(cols), rowlen,
                                 len(rows)) + body + bytes(size - 24 - len(body))


def _itoc(ents):
    """ITOC packet for [(id, csize, size)]. Sizes that fit u16 go in the L table, the rest in H, each sorted by ID."""
    ents = sorted(ents)
    low = [e for e in ents if e[1] < 0x10000 and e[2] < 0x10000]
    high = [e for e in ents if e[1] >= 0x10000 or e[2] >= 0x10000]
    cols = (b"ID", 0x52), (b"FileSize", 0x52), (b"ExtractSize", 0x52)
    tl = _table(b"CpkItocL", cols, ">HHH", low)
    cols = (b"ID", 0x52), (b"FileSize", 0x54), (b"ExtractSize", 0x54)
    th = _table(b"CpkItocH", cols, ">HII", high)
    strs = b"<NULL>\0CpkItocInfo\0FilesL\0FilesH\0DataL\0DataH\0"
    head = b"".join(bytes([f]) + struct.pack(">I", strs.index(n + b"\0"))
                    for n, f in ((b"FilesL", 0x54), (b"FilesH", 0x54), (b"DataL", 0x5B), (b"DataH", 0x5B)))
    row = struct.pack(">IIIIII", len(low), len(high), 0, len(tl), len(tl), len(th))
    data_off = 120  # fixed: 44 rows_off + 24 row + 45 strings, padded
    size = data_off + len(tl) + len(th)
    utf = (b"@UTF" + struct.pack(">IIIIIHHI", size, 44, 68, data_off, 7, 4, 24, 1) + head + row + strs
           + bytes(data_off - 68 - len(strs)) + tl + th)
    return b"ITOC" + b"\xff\0\0\0" + struct.pack("<II", len(utf), 0) + utf


def rebuild(path, repl, keep_same=True):
    """Data.cpk with {id: uncompressed bytes} replaced; other blocks are copied, so no edits gives the original bytes.
    Edited files are stored, not recompressed (the engine reads stored files: docs/re/text.md). keep_same keeps the
    original block when the replacement equals its contents."""
    with open(path, "rb") as f:
        head = bytearray(f.read(0x800))
        info = Utf(bytes(head), 16)
        ents, blocks = [], []
        for fid, off, csize, size in read_entries(path):
            f.seek(off)
            d = f.read(csize)
            if fid in repl:
                new = repl[fid]
                same = keep_same and (d[:8] == b"CRILAYLA" and csize != size and crilayla_decompress(d) == new or d == new)
                if not same:
                    d, size = new, len(new)
            ents.append((fid, len(d), size))
            blocks.append(d)
    missing = set(repl) - {e[0] for e in ents}
    assert not missing, f"no such file ids: {sorted(missing)}"
    r = info.rows[0]
    align = r["Align"]
    itoc = _itoc(ents)
    # room for ~366 L rows moving to H before the content has to shift
    content = max(r["ContentOffset"], -(-(r["ItocOffset"] + len(itoc)) // align) * align)
    out = bytearray(content)
    out[:0x800] = head
    out[r["ItocOffset"]:r["ItocOffset"] + len(itoc)] = itoc
    pad = [bytes(-len(d) % align) for d in blocks[:-1]] + [b""]
    body = b"".join(x for pair in zip(blocks, pad) for x in pair)
    for col, v in (("ContentOffset", content), ("ContentSize", -(-len(body) // align) * align), ("ItocSize", len(itoc)),
                   ("EnabledDataSize", sum(e[1] for e in ents)), ("EnabledPackedSize", sum(e[2] for e in ents))):
        info.set(out, 0, col, v)
    return bytes(out) + body


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
