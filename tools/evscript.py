"""Event-script recon (CPK IDs 2149-2205). usage: evscript.py FILE [--text] [--ops]
Header: 10 u32 (u32[0] = file size - 0x14); text section from 0x28 to u32[1]; bytecode [op u8, len u8, args] after it."""
import collections
import struct
import sys


def header(d):
    return struct.unpack_from("<10I", d)


def text_entries(d):
    """-> [(file offset, tag or None, raw bytes)]. Records are '02 00 <tag u16> text 00' or a bare 'text 00'."""
    end, p, out = header(d)[1], 0x28, []
    while p < end:
        tag = None
        start = p
        if d[p] == 2 and d[p + 1] == 0:
            tag = struct.unpack_from("<H", d, p + 2)[0]
            p += 4
        q = d.index(0, p)
        out.append((start, tag, d[p:q]))
        p = q + 1
    return out


def walk_ops(d, start, end):
    """Walk [op, len, ...] from start; stop at a len < 2 or past end. -> [(off, op, raw)], stop offset."""
    p, out = start, []
    while p < end:
        op, ln = d[p], d[p + 1]
        if ln < 2 or p + ln > len(d):
            break
        out.append((p, op, d[p:p + ln]))
        p += ln
    return out, p


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    h = header(d)
    print("header", [hex(x) for x in h], "size", hex(len(d)))
    ents = text_entries(d)
    print("entries", len(ents), "tagged", sum(e[1] is not None for e in ents), "tags", ents[0][1], "..", ents[-1][1],
          "text end", hex(ents[-1][0] + len(ents[-1][2]) + 1))
    if "--text" in sys.argv:
        for o, t, s in ents:
            print(hex(o), t, s.replace(b"\x01", b"/").decode("cp932", "backslashreplace"))
    if "--ops" in sys.argv:
        ops, stop = walk_ops(d, h[1], len(d))
        print("walked", len(ops), "ops to", hex(stop), "of", hex(len(d)))
        c = collections.Counter((o[1], len(o[2])) for o in ops)
        print(sorted(c.items(), key=lambda kv: -kv[1])[:60])
