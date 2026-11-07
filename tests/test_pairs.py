import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import pairs


def test_chunks_keep_batches_whole_and_keep_the_tail():
    assert pairs.chunks([("a", 2), ("b", 2), ("c", 1)], 3) == [["a", "b"], ["c"]]
    assert pairs.chunks([("a", 3), ("b", 3)], 3) == [["a"], ["b"]]
