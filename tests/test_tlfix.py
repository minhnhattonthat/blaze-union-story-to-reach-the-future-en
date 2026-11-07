import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import tlfix


def test_set_lines_replaces_only_the_named_lines():
    assert tlfix.set_lines("1\ta\n2\tb\n", {2: "c"}) == "1\ta\n2\tc\n"


def test_set_lines_refuses_a_line_that_is_not_there():
    with pytest.raises(AssertionError):
        tlfix.set_lines("1\ta\n", {9: "c"})
