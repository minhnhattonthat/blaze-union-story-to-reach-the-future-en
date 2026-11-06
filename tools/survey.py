"""Recon: per magic, file count, size range, ID range and Shift-JIS / UTF-16LE density across the unpacked CPK.
usage: survey.py work/cpk"""
import re
import sys
from collections import defaultdict
from pathlib import Path

SJIS = re.compile(rb"(?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc]){4,}")
U16 = re.compile(rb"(?:[\x41-\x93\xa0-\xff][\x30\x4e-\x9f]){4,}")


def key(d):
    m = d[:4]
    if all(32 <= c < 127 for c in m[:3]):
        return m[:3].decode()
    if m[:2] == b"\x80\x00":
        return "ADX"
    return "x" + m.hex()[:4]


stats = defaultdict(lambda: [0, 0, 1 << 40, -1, 0, 0, []])
for p in sorted(Path(sys.argv[1]).glob("*.bin")) + sorted(Path(sys.argv[1]).glob("*.png")):
    d = p.read_bytes()
    k = key(d)
    s = stats[k]
    fid = int(p.stem)
    s[0] += 1
    s[1] += len(d)
    s[2] = min(s[2], fid)
    s[3] = max(s[3], fid)
    sj = sum(len(m) for m in SJIS.findall(d))
    u = sum(len(m) for m in U16.findall(d))
    s[4] += sj
    s[5] += u
    if sj + u > 64 and len(s[6]) < 6:
        s[6].append(f"{fid}:{sj}/{u}")
for k, s in sorted(stats.items(), key=lambda kv: -kv[1][0])[:40]:
    print(f"{k:8} n={s[0]:5} bytes={s[1]:10} ids={s[2]}-{s[3]} sjis={s[4]} u16={s[5]} {' '.join(s[6])}")
