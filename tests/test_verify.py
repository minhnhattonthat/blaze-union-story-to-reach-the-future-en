"""The English EBOOT changes only what the build logged, and the defeat table's parts each fit one line of their window."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools/debug"))
import build
import defeat_parts
import fit
import insert
import verify_build


def test_eboot_writes_match(tmp_path):
    _, eboot, _ = insert.build(build.Translated())
    assert verify_build.check_eboot(eboot) == []


def test_defeat_parts_have_their_windows():
    news, over, chains = defeat_parts.ids((ROOT / "work/exe/code.bin").read_bytes())
    assert news and over and not news & over
    boxes = fit.boxes()
    assert {boxes[i] for i in over} == {"game_over_text"}
    assert all(len(c) <= 5 for c in chains)  # the window has 5 rows
