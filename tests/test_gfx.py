"""gfx.py writes sprites back: every PTX's indices re-encode to its bytes, and every group of FCT 3 repacked from its own
render draws the same pixels within its slices and cell count. Needs the unpacked work/cpk (skipped without it)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx
import ptg

FCT3 = ROOT / "work/cpk/00003.bin"
pytestmark = pytest.mark.skipif(not FCT3.exists(), reason="work/cpk not unpacked")


@pytest.fixture(scope="module")
def fct3():
    return FCT3.read_bytes()


def test_ptx_indices_roundtrip(fct3):
    for first, (kind, off) in gfx.sprites(fct3).items():
        slices = ptg.parse(fct3, off)["slices"] if kind == "ptg" else [off]
        for s in slices:
            d = bytearray(fct3)
            gfx.put_indices(d, s, gfx.indices(fct3, s))
            assert d == fct3, hex(s)


def test_repack_draws_the_same(fct3):
    for first, (kind, off) in gfx.sprites(fct3).items():
        if kind != "ptg":
            continue
        img = ptg.render(fct3, off, pal=gfx.group_palette(fct3, off))
        d = bytearray(fct3)
        gfx.repack(d, off, img)
        a, b = gfx.span(fct3, off)
        assert len(d) == len(fct3) and d[:a] == fct3[:a] and d[b:] == fct3[b:], hex(off)
        new = ptg.render(bytes(d), off, pal=gfx.group_palette(fct3, off)).crop((0, 0) + img.size)
        assert seen(new) == seen(img), hex(off)


def seen(img):
    """Pixels with fully transparent ones normalised: a clear pixel's colour never shows."""
    return bytes(b for p in img.getdata() for b in (p if p[3] else (0, 0, 0, 0)))
