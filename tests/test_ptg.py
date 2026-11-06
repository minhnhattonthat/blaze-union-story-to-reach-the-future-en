"""PTG sprite groups: cells of each list come from their own slice and land at their destination."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ptg import parse, render

RED, BLUE = 0xFF0000FF, 0xFFFF0000


def slice_(colour, with_palette=True):
    """2x1 T8 linear PTX whose pixels are both palette index 0."""
    poff = 0x20 if with_palette else 0
    pal = struct.pack("<I", colour) if with_palette else b""
    doff = 0x20 + len(pal)
    head = b"PTX@" + struct.pack("<BBHHHBBBBIIII", 1, 0, 2, 2, 1, 5, 0, 0, 0, 1, 0, poff, doff)
    return head + pal + bytes(2)


def group(second, n1):
    first = slice_(RED)
    cells = [(0, 0, 0, 0, 0, 2, 1, 2, 1, 0)] + [(0, 0, 2, 0, 0, 2, 1, 4, 1, 0)] * n1
    table = b"".join(struct.pack("<10H", *c) for c in cells)
    p0 = 0x20 + len(table)
    head = b"PTG@" + struct.pack("<IIIHHHH", 0x20, p0, p0 + len(first) if second else 0, 4, 1, 1, n1) + bytes(8)
    return head + table + first + second


def test_second_cell_list_reads_second_slice():
    d = group(slice_(BLUE), 1)
    g = parse(d)
    assert (g["n0"], g["n1"], g["w"], g["h"], len(g["slices"])) == (1, 1, 4, 1, 2)
    img = render(d)
    assert img.getpixel((0, 0))[:3] == (255, 0, 0) and img.getpixel((2, 0))[:3] == (0, 0, 255)


def test_second_slice_without_palette_uses_the_first():
    assert render(group(slice_(0, with_palette=False), 1)).getpixel((3, 0))[:3] == (255, 0, 0)


@pytest.mark.skipif(not (ROOT / "work/cpk/00111.bin").is_file(), reason="needs work/cpk from itoc.py x")
def test_real_two_slice_banner():
    d = (ROOT / "work/cpk/00111.bin").read_bytes()
    g = parse(d)
    assert (g["n0"], g["n1"]) == (20, 10) and len(g["cells"]) == 30
    img = render(d)
    # slice 0's cells stop at y=32, so ink below that proves slice 1's list was drawn
    assert img.size == (443, 49) and img.getbbox()[3] > 32
