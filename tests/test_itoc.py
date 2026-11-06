"""ITOC reader and CRILAYLA decoder against the real Data.cpk (skips on a clone with no extracted image)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from itoc import crilayla_decompress, read_entries

CPK = ROOT / "work/iso/PSP_GAME/USRDIR/Data/Data.cpk"


def test_rejects_non_crilayla():
    with pytest.raises(AssertionError):
        crilayla_decompress(b"NOTLAYLA" + bytes(32))


@pytest.mark.skipif(not CPK.is_file(), reason="needs work/iso from iso9660.py x")
def test_entries_cover_cpk_and_decompress():
    ents = read_entries(CPK)
    assert len(ents) == 3340 and [e[0] for e in ents] == list(range(3340))
    assert ents[-1][1] + ents[-1][2] == CPK.stat().st_size  # last file ends exactly at EOF
    with open(CPK, "rb") as f:
        done = 0
        for fid, off, csize, size in ents:
            if csize != size and size < 200_000:
                f.seek(off)
                assert len(crilayla_decompress(f.read(csize))) == size, fid
                done += 1
                if done == 30:
                    break
    assert done == 30
