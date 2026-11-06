"""Identity build: unpack then repack with no edits gives the original disc, byte for byte. Needs the dump (skips on a clone)."""
import hashlib
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import iso9660
import itoc

pytestmark = pytest.mark.skipif(not build.ROM.is_file(), reason="needs the dump in rom/")


@pytest.fixture(scope="module")
def cpk(tmp_path_factory):
    p = tmp_path_factory.mktemp("cpk") / "Data.cpk"
    p.write_bytes(build.extract(build.ROM, build.CPK))
    return p


def sha1(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha1").hexdigest()


def test_disc_identical(tmp_path):
    out = build.build(tmp_path / "out.iso", repl={})
    assert out.stat().st_size == build.ROM.stat().st_size
    want = (ROOT / "rom.sha1").read_text().split("\n")[1].split()[0]
    assert sha1(out) == want


def test_unpacked_files_repack_to_the_same_archive(cpk):
    """Handing back a file's unpacked bytes, compressed or stored, keeps the original block."""
    ents = itoc.read_entries(cpk)
    packed = [e for e in ents if e[2] != e[3] and e[3] < 100_000][:20]
    stored = [e for e in ents if e[2] == e[3] and e[3] < 100_000][:20]
    assert len(packed) == len(stored) == 20
    repl = {}
    with open(cpk, "rb") as f:
        for fid, off, csize, _ in packed + stored:
            f.seek(off)
            d = f.read(csize)
            repl[fid] = itoc.crilayla_decompress(d) if d[:8] == b"CRILAYLA" else d
    assert itoc.rebuild(cpk, repl) == cpk.read_bytes()


def test_edit_moves_only_what_it_should(cpk, tmp_path):
    """A compressed file under 64K grown past it: stored, moved to the H table, every other file's bytes intact."""
    orig = {e[0]: e for e in itoc.read_entries(cpk)}
    fid = 2149
    assert orig[fid][2] != orig[fid][3] and orig[fid][3] < 0x10000
    new = bytes(range(256)) * 300  # 76800 bytes
    data = itoc.rebuild(cpk, {fid: new})
    out = tmp_path / "new.cpk"
    out.write_bytes(data)
    ents = itoc.read_entries(out)
    assert [e[0] for e in ents] == sorted(orig)
    src = cpk.read_bytes()
    for e in ents:
        o = orig[e[0]]
        if e[0] == fid:
            assert e[2] == e[3] == len(new) and data[e[1]:e[1] + e[2]] == new
        else:
            assert e[2:] == o[2:] and data[e[1]:e[1] + e[2]] == src[o[1]:o[1] + o[2]], e[0]
    info = itoc.Utf(data[:0x800], 16).rows[0]
    tb = data[info["ItocOffset"]:info["ItocOffset"] + info["ItocSize"]]
    t = itoc.Utf(tb, 16).rows[0]
    assert (t["FilesL"], t["FilesH"]) == (2141, 1199)
    assert info["ContentOffset"] % 2048 == 0
    assert info["ContentSize"] == -(-(len(data) - info["ContentOffset"]) // 2048) * 2048
    assert info["EnabledDataSize"] == sum(e[2] for e in ents)
    assert info["EnabledPackedSize"] == sum(e[3] for e in ents)


def test_bigger_archive_moves_to_end_of_image(tmp_path):
    """Directory record and volume size follow; the original bytes before the new end stay readable."""
    new = bytes(449_000_000)
    out = tmp_path / "out.iso"
    iso9660.patch(str(build.ROM), str(out), {build.CPK: new})
    with open(out, "rb") as f:
        ls = {e[0]: e for e in iso9660.listing(f)}
        _, lba, size, _ = ls[build.CPK]
        assert size == len(new) and lba * 2048 == build.ROM.stat().st_size
        f.seek(16 * 2048 + 80)
        assert struct.unpack("<I", f.read(4))[0] * 2048 == out.stat().st_size
