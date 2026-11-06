"""Recon: find real Japanese sentences in every unpacked file. Noise filter: a run must decode as cp932 and be at least
half kana/common punctuation or have 2+ kana, so random texture bytes rarely pass.
usage: textscan.py DIR [--min N]  -> one line per file with real strings: id, count, chars, UTF-16 count, first string"""
import re
import sys
from pathlib import Path

SJ = re.compile(rb"(?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc]){3,}")
U16 = re.compile(rb"(?:[\x40-\xff][\x30]|[\x00-\xff][\x4e-\x9f]){4,}")
KANA = re.compile("[ぁ-ゖァ-ヺ]")


def real(s):
    kana = len(KANA.findall(s))
    return kana >= 2 and kana * 3 >= len(s)


def scan(d):
    sj = []
    for m in SJ.finditer(d):
        try:
            s = m.group().decode("cp932")
        except UnicodeDecodeError:
            continue
        if real(s):
            sj.append((m.start(), s))
    u = []
    for m in U16.finditer(d):
        b = m.group()
        s = b[: len(b) & ~1].decode("utf-16le", "ignore")
        if real(s):
            u.append((m.start(), s))
    return sj, u


if __name__ == "__main__":
    root = Path(sys.argv[1])
    mn = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 3
    tot = 0
    for p in sorted(root.iterdir()):
        if p.suffix not in (".bin", ".png"):
            continue
        sj, u = scan(p.read_bytes())
        if len(sj) >= mn or len(u) >= mn:
            n = sum(len(s) for _, s in sj)
            tot += n
            first = (sj or u)[len(sj or u) // 2][1][:24]
            print(f"{p.stem}\t{p.stat().st_size}\tsj={len(sj)}\tchars={n}\tu16={len(u)}\t{p.read_bytes()[:4].hex()}\t{first}")
    print("total sjis chars", tot)
