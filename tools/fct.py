"""FCT container: 'FCT\\0', u32 count, u32 table offset, then (u32 offset, u32 size) per child.
Library: children(bytes) -> [(off, size)]. CLI: fct.py x FILE OUTDIR"""
import struct
import sys
from pathlib import Path


def children(d):
    assert d[:4] == b"FCT\0", d[:4]
    n, tab = struct.unpack_from("<II", d, 4)
    return [struct.unpack_from("<II", d, tab + i * 8) for i in range(n)]


if __name__ == "__main__":
    assert sys.argv[1] == "x"
    d = Path(sys.argv[2]).read_bytes()
    out = Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    for i, (o, s) in enumerate(children(d)):
        (out / f"{i:03d}.bin").write_bytes(d[o:o + s])
