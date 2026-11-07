import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import tm


def test_fill_prefers_part_and_ignores_breaks():
    done, missing = tm.fill(["あ{n}い", "う", "え"], {"あい": "Ai", "う": "U"}, {2: "Mine"})
    assert done == {1: "Ai", 2: "Mine"}
    assert missing == [3]
