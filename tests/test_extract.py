"""Extraction against the original files: every record re-encodes to its bytes, every reference points at its record, and no
Japanese sentence or unexplained byte is left outside a record. Needs work/cpk and work/exe (AGENTS.md, Unpack)."""
import json
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import evscript
import extract as X

pytestmark = pytest.mark.skipif(not (ROOT / "work/cpk/02149.bin").exists() or not X.ELF.exists(), reason="unpacked game needed")


@pytest.fixture(scope="module")
def dump():
    files, info = X.extract()
    return files, info, X.sources()


def images(src, name):
    d, kind = src[name]
    return d[0x74:] if kind == "eboot" else d


def eboot_records(files):
    return [r for n, es in files.items() if n.startswith("eboot_") for r in es]


def test_roundtrip(dump):
    """encode(decode(bytes)) == bytes for every string, control codes included."""
    files, _, src = dump
    n = 0
    for name, ents in files.items():
        d = images(src, "eboot" if name.startswith("eboot_") else name)
        for r in ents:
            assert X.TBL.encode(r["jp"]) + b"\0" == d[r["ptr"]:r["ptr"] + r["bytes"]], r["id"]
            n += 1
    assert n > 20000


def test_slots_point_at_their_string(dump):
    files, _, src = dump
    img = images(src, "eboot")
    for r in eboot_records(files):
        for s in r["slots"]:
            if "word" in s:
                assert struct.unpack_from("<I", img, s["word"])[0] == r["ptr"], r["id"]
            else:
                hi = struct.unpack_from("<H", img, s["hi"])[0]
                lo = struct.unpack_from("<h", img, s["lo"])[0]
                assert (hi << 16) + lo == r["ptr"], r["id"]
    for name, ents in files.items():
        if name.startswith("eboot_") or name == "fct1_0":
            continue
        d = src[name][0]
        for r in ents:
            for s in r["slots"]:
                if r["kind"] == "inline":
                    assert d[s] == evscript.INLINE and s + 3 == r["ptr"], r["id"]
                else:
                    assert d[s - 3] == 0x46 and struct.unpack_from("<I", d, s)[0] == r["ptr"], r["id"]


def test_no_japanese_left_out(dump):
    """Every sentence textscan's filter finds in a text file belongs to a record."""
    files, _, src = dump
    for name, (d, kind) in src.items():
        if kind == "script":
            assert not X.uncovered(d, files[name]), name
    img = images(src, "eboot")[:X.DATA_END + 1]
    assert not [u for u in X.uncovered(img, eboot_records(files)) if u[0] >= X.RODATA]


def test_scripts_fully_covered(dump):
    """Every byte of a script is header, code, string, padding or a small explained data span with no text in it."""
    _, info, src = dump
    assert sum(s.get("code", 0) for s, _ in info.values()) > 2_000_000
    for name, (stats, other) in info.items():
        d = src[name][0]
        assert stats.get("other", 0) < 500, name
        for a, b in other:
            assert not X.textscan.scan(d[a:b])[0], (name, hex(a))


def test_known_lines(dump):
    """Anchors checked by hand against the docs and the game."""
    files, _, _ = dump
    by_id = {r["id"]: r for r in eboot_records(files)}
    assert by_id["eboot_2596E4"]["jp"].startswith("ジルヴァ")
    assert {"word": 0x2ADF24} in by_id["eboot_2596E4"]["slots"]
    event = {r["ptr"]: r for r in files["event_2149"]}
    assert event[0x28]["kind"] == "msg" and event[0x28]["jp"].startswith("{voice:")
    assert sum(r["kind"] == "inline" for r in files["event_2149"]) == 2  # ブレイズ義賊団, ノルン一味
    assert any(r["jp"] == "ブレイズ義賊団" for r in files["event_2149"])


def test_json_matches_a_fresh_dump(dump):
    """script/*.json stay in step with the extractor. A later phase fills en and status, nothing else changes."""
    files, _, _ = dump
    for name, ents in files.items():
        path = X.OUT / f"{name}.json"
        assert path.exists(), name
        saved = json.loads(path.read_text(encoding="utf-8"))
        assert [(r["id"], r["jp"], r["slots"], r["kind"]) for r in saved] == [(r["id"], r["jp"], r["slots"], r["kind"]) for r in ents], name
